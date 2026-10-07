import hashlib
import json
import os
from decimal import Decimal

import pytest

from ttd_lab import database
from ttd_lab.contracts import ContractError
from ttd_lab.fixtures import generate

pytestmark = pytest.mark.integration


@pytest.fixture
def warehouse(tmp_path):
    url = os.environ.get("LAB_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set LAB_TEST_DATABASE_URL for PostgreSQL integration tests")
    psycopg = pytest.importorskip("psycopg")
    from psycopg.conninfo import conninfo_to_dict
    settings = conninfo_to_dict(url)
    assert settings["dbname"] == "ttd_lab_test" and settings["host"] in {"127.0.0.1", "localhost"}, \
        "Integration tests require the dedicated local ttd_lab_test database"
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute("DROP SCHEMA IF EXISTS lab CASCADE")
    database.initialize(url)
    generate(tmp_path, profile="unit")
    database.ingest(url, tmp_path / "baseline")
    with psycopg.connect(url, autocommit=True) as connection:
        yield url, tmp_path, connection


def value(connection, query, params=()):
    return connection.execute(query, params).fetchone()[0]


def final_spend(connection, account):
    return value(connection, "SELECT spend_usd FROM lab.account_day_working WHERE account_id=%s AND business_date='2026-08-31'", (account,))


def test_replay_is_noop_and_totals_reconcile(warehouse):
    url, root, con = warehouse
    result = database.ingest(url, root / "baseline")
    assert result["accepted_files"] == 0
    assert result["replayed_files"] == 170
    assert value(con, "SELECT COUNT(*) FROM lab.raw_files") == 170
    assert value(con, "SELECT COUNT(*) FROM lab.account_day_working") == 560
    assert value(con, "SELECT SUM(spend_usd) FROM lab.delivery") == value(con, "SELECT SUM(spend_usd) FROM lab.account_day_working")


def test_missing_zero_and_planned_ending_have_distinct_states(warehouse):
    _, _, con = warehouse
    assert final_spend(con, "harbor") is None
    assert final_spend(con, "maple") == Decimal("0")
    assert final_spend(con, "beacon") == Decimal("0")
    rows = dict(con.execute("SELECT account_id, data_state FROM lab.account_day_working WHERE business_date='2026-08-31'"))
    assert rows["harbor"] == "missing_delivery"
    assert rows["maple"] == "complete"
    assert rows["beacon"] == "inactive"


def test_correction_retains_exact_old_bytes_and_old_replay_cannot_revert(warehouse):
    url, root, con = warehouse
    baseline = root / "baseline/delivery/2026-08-31_display_v1.json"
    before = baseline.read_bytes()
    database.ingest(url, root / "events/correct_atlas")
    assert final_spend(con, "atlas") == Decimal("400000")
    assert value(con, "SELECT SUM(spend_usd) FROM lab.account_day_working WHERE account_id='atlas' AND business_date BETWEEN '2026-08-25' AND '2026-08-31'") == Decimal("1300000")
    stored = value(con, "SELECT raw_bytes FROM lab.raw_files WHERE checksum=%s", (hashlib.sha256(before).hexdigest(),))
    assert bytes(stored) == before
    database.ingest(url, baseline)
    assert final_spend(con, "atlas") == Decimal("400000")
    assert value(con, "SELECT COUNT(*) FROM lab.raw_files WHERE source='delivery' AND partition_key='2026-08-31:display'") == 2


def test_late_file_recovers_missing_day(warehouse):
    url, root, con = warehouse
    database.ingest(url, root / "events/late_harbor")
    assert final_spend(con, "harbor") == Decimal("400000")
    assert value(con, "SELECT COUNT(*) FROM lab.account_day_working WHERE data_state='missing_delivery'") == 0


def test_same_version_different_bytes_rejected_and_failure_recorded(warehouse):
    url, root, con = warehouse
    bad = root / "conflict.json"
    document = json.loads((root / "baseline/delivery/2026-08-31_display_v1.json").read_text())
    document["rows"][0]["spend_usd"] = "999.00"
    bad.write_text(json.dumps(document))
    with pytest.raises(ContractError, match="Conflicting or stale"):
        database.ingest(url, bad)
    assert final_spend(con, "atlas") == Decimal("150000")
    assert value(con, "SELECT COUNT(*) FROM lab.raw_files") == 170
    assert value(con, "SELECT COUNT(*) FROM lab.ingestion_runs WHERE status='failed'") == 1


def test_valid_removal_changes_current_partition_preserves_history(warehouse):
    url, root, con = warehouse
    database.ingest(url, root / "events/retire_atlas")
    assert final_spend(con, "atlas") == Decimal("0")
    assert value(con, "SELECT data_state FROM lab.account_day_working WHERE account_id='atlas' AND business_date='2026-08-31'") == "inactive"
    assert value(con, "SELECT COUNT(*) FROM lab.raw_files") == 173
    assert value(con, "SELECT COUNT(*) FROM lab.delivery WHERE campaign_id='campaign-atlas' AND business_date='2026-08-31'") == 0


def test_failure_after_write_rolls_back_then_retry_recovers(warehouse, monkeypatch):
    url, root, con = warehouse
    original = database._write_file

    def interrupted(*args):
        original(*args)
        raise RuntimeError("Injected failure after database writes")

    monkeypatch.setattr(database, "_write_file", interrupted)
    with pytest.raises(RuntimeError, match="Injected failure"):
        database.ingest(url, root / "events/correct_atlas")
    assert value(con, "SELECT COUNT(*) FROM lab.raw_files") == 170
    assert final_spend(con, "atlas") == Decimal("150000")
    assert value(con, "SELECT COUNT(*) FROM lab.ingestion_runs WHERE status='failed'") == 1
    monkeypatch.setattr(database, "_write_file", original)
    database.ingest(url, root / "events/correct_atlas")
    assert final_spend(con, "atlas") == Decimal("400000")


def test_multi_campaign_account_totals_do_not_fan_out(warehouse):
    url, root, con = warehouse
    con.execute("DROP SCHEMA lab CASCADE")  # Dedicated local test database only.
    database.initialize(url)
    dataset = root / "commercial"
    summary = generate(dataset, profile="commercial", account_count=20,
                       campaigns_per_account=3, days=14)
    database.ingest(url, dataset / "baseline")
    assert value(con, "SELECT COUNT(*) FROM lab.delivery") == summary["delivery_rows"]
    assert value(con, "SELECT COUNT(*) FROM lab.account_day_working") == 280
    assert final_spend(con, "atlas") == Decimal("150000")
    assert value(con, "SELECT planned_spend_usd FROM lab.account_day_working WHERE account_id='atlas' AND business_date='2026-08-31'") == Decimal("500000")
    assert value(con, "SELECT SUM(spend_usd) FROM lab.delivery") == value(con, "SELECT SUM(spend_usd) FROM lab.account_day_working")
    database.ingest(url, dataset / "events/correct_atlas")
    assert final_spend(con, "atlas") == Decimal("400000")


def test_executive_report_matches_independent_expectations_and_source_events(warehouse):
    from pathlib import Path
    from ttd_lab.reporting import build_report

    url, root, _ = warehouse
    expected = json.loads(Path(__file__).with_name("scenario_expectations.json").read_text())
    report = build_report(database.account_days(url), "2026-08-31")
    accounts = {account["id"]: account for account in report["accounts"]}
    for identity, values in expected["accounts"].items():
        actual = accounts[identity]
        assert actual["route"] == values["next_classification"]
        assert actual["prior"]["spend_cents"] == int(Decimal(values["prior_spend"]) * 100)
        assert actual["current"]["spend_cents"] == (None if values["current_spend"] is None else int(Decimal(values["current_spend"]) * 100))
    database.ingest(url, root / "events/correct_atlas")
    database.ingest(url, root / "events/late_harbor")
    revised = build_report(database.account_days(url), "2026-08-31")
    new = {account["id"]: account for account in revised["accounts"]}
    assert new["atlas"]["current"]["spend_cents"] == 130000000
    assert new["harbor"]["current"]["spend_cents"] == 280000000
    assert new["harbor"]["route"] == "no_decline_signal"
    assert revised["snapshot_id"] != report["snapshot_id"]
