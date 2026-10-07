import argparse
import csv
import json
import os
import sys
from pathlib import Path

from .contracts import load_files, validate_state
from .fixtures import generate


def main():
    parser = argparse.ArgumentParser(description="Fictional commercial intelligence lab")
    commands = parser.add_subparsers(dest="command", required=True)
    fixture = commands.add_parser("generate", help="Generate fixed fictional inputs and correction events")
    fixture.add_argument("--output", type=Path, default=Path("data/fixtures"))
    fixture.add_argument("--seed", type=int, default=42)
    validate = commands.add_parser("validate", help="Validate a complete source directory without a database")
    validate.add_argument("path", type=Path)
    commands.add_parser("init-db", help="Create lab schema and SQL views; preserves existing data")
    load = commands.add_parser("load", help="Atomically accept source files or replay them")
    load.add_argument("path", type=Path)
    export = commands.add_parser("export", help="Export the account-day working view; not a published signal queue")
    export.add_argument("--output", type=Path, default=Path("outputs/account_day_working.csv"))
    args = parser.parse_args()
    try:
        if args.command == "generate":
            result = generate(args.output, args.seed)
        elif args.command == "validate":
            documents = {}
            inputs = load_files(args.path)
            for _, _, doc in inputs:
                identity = doc["source"], doc["partition"]
                if identity in documents:
                    raise ValueError("Standalone validation requires one file per partition")
                documents[identity] = doc
            validate_state(documents)
            result = {"status": "valid", "files": len(inputs)}
        else:
            from .database import initialize, ingest, account_days
            database_url = os.environ.get("LAB_DATABASE_URL", "postgresql://ttd_lab:ttd_lab_local@127.0.0.1:55432/ttd_lab")
            if args.command == "init-db":
                initialize(database_url)
                result = {"status": "schema_ready"}
            elif args.command == "load":
                result = ingest(database_url, args.path)
            else:
                rows = account_days(database_url)
                if not rows:
                    raise ValueError("No accepted account-day data; load fixtures first")
                args.output.parent.mkdir(parents=True, exist_ok=True)
                with args.output.open("w", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                    writer.writeheader()
                    for row in rows:
                        row["evidence"] = json.dumps(row["evidence"], sort_keys=True)
                        # CSV empty spend means unknown; observed zero is written as 0.
                        writer.writerow(row)
                result = {"output": str(args.output), "rows": len(rows),
                          "missing_account_days": sum(r["data_state"] == "missing_delivery" for r in rows)}
        print(json.dumps(result, sort_keys=True))
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
