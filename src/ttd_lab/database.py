"""Atomic source acceptance with immutable raw history and persistent run failures."""

import hashlib
import uuid
from importlib.resources import files
from pathlib import Path

from .contracts import load_files, require, validate_state


def initialize(database_url):
    import psycopg
    with psycopg.connect(database_url) as connection:
        connection.execute(files("ttd_lab").joinpath("schema.sql").read_text())


def _write_file(connection, path, raw, document, checksum, run_id):
    from psycopg.types.json import Jsonb
    file_id = connection.execute(
        """INSERT INTO lab.raw_files
           (source, partition_key, source_version, checksum, filename, row_count,
            raw_bytes, payload, accepted_run_id)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING file_id""",
        (document["source"], document["partition"], document["version"], checksum,
         str(path), len(document["rows"]), raw, Jsonb(document), run_id)
    ).fetchone()[0]
    connection.execute(
        """INSERT INTO lab.current_files (source, partition_key, file_id)
           VALUES (%s,%s,%s) ON CONFLICT (source, partition_key)
           DO UPDATE SET file_id = EXCLUDED.file_id""",
        (document["source"], document["partition"], file_id))


def ingest(database_url, path: Path):
    import psycopg
    run_id = uuid.uuid4()
    with psycopg.connect(database_url, autocommit=True) as connection:
        connection.execute(
            "INSERT INTO lab.ingestion_runs (run_id, input_path, status) VALUES (%s,%s,'running')",
            (run_id, str(path)))
        try:
            with connection.transaction():
                # Serializes lab source acceptance, including concurrent replays.
                connection.execute("SELECT pg_advisory_xact_lock(7729001)")
                current = {(source, partition): payload for source, partition, payload in connection.execute(
                    "SELECT source, partition_key, payload FROM lab.accepted_files")}
                known = {checksum for (checksum,) in connection.execute("SELECT checksum FROM lab.raw_files")}
                pending = []
                incoming = {}
                replayed = 0
                for filename, raw, document in load_files(path):
                    checksum = hashlib.sha256(raw).hexdigest()
                    identity = document["source"], document["partition"]
                    require(identity not in incoming or incoming[identity] == checksum,
                            "A load may contain only one version per source partition")
                    incoming[identity] = checksum
                    if checksum in known:
                        replayed += 1
                        continue
                    previous = current.get(identity)
                    require(previous is None or document["version"] > previous["version"],
                            f"Conflicting or stale source version: {identity}")
                    current[identity] = document
                    pending.append((filename, raw, document, checksum))
                    known.add(checksum)
                validate_state(current)
                for filename, raw, document, checksum in pending:
                    _write_file(connection, filename, raw, document, checksum, run_id)
                connection.execute(
                    """UPDATE lab.ingestion_runs SET status='succeeded', finished_at=now(),
                       accepted_files=%s, replayed_files=%s WHERE run_id=%s""",
                    (len(pending), replayed, run_id))
            return {"run_id": str(run_id), "status": "succeeded",
                    "accepted_files": len(pending), "replayed_files": replayed}
        except Exception as exc:
            connection.execute(
                "UPDATE lab.ingestion_runs SET status='failed', finished_at=now(), error=%s WHERE run_id=%s",
                (str(exc), run_id))
            raise


def account_days(database_url):
    import psycopg
    from psycopg.rows import dict_row
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        return connection.execute(
            "SELECT * FROM lab.account_day_working ORDER BY business_date, account_id").fetchall()
