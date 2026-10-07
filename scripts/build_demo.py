"""Build the public walkthrough from a reconciled baseline export, not browser fixtures.

Run after `ttd-lab generate`, baseline ingestion, and `ttd-lab export` on a fresh
database. Refuse corrected or differently sized data rather than silently
publishing a snapshot that no longer matches the documented scenario.
"""

import csv
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def cents(value):
    return None if value in (None, "") else int(Decimal(value) * 100)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def build():
    fixture = ROOT / "data/fixtures-commercial"
    manifest = json.loads((fixture / "scale_manifest.json").read_text())
    expected = json.loads((ROOT / "tests/scenario_expectations.json").read_text())
    with (ROOT / "outputs/account_day_working.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    require(manifest["accounts"] == 1000 and manifest["campaigns"] == 5000
            and manifest["business_dates"] == 56 and manifest["seed"] == 42,
            "The public demo requires the default commercial profile, seed 42")
    require(len(rows) == manifest["account_day_rows"], "Account-day count mismatch")
    require(sum(cents(row["spend_usd"]) or 0 for row in rows) == cents(manifest["baseline_spend_usd"]),
            "Export does not reconcile to baseline spend; use a fresh database")
    require(sum(int(row["impressions"] or 0) for row in rows) == manifest["baseline_paid_impressions"],
            "Export does not reconcile to paid impressions")
    require(sum(row["data_state"] == "missing_delivery" for row in rows) == 1,
            "Expected exactly one missing account-day")
    accounts = []
    periods = expected["periods"]
    for account_id, expectation in expected["accounts"].items():
        days = sorted((row for row in rows if row["account_id"] == account_id
                       and periods["prior_start"] <= row["business_date"] <= periods["current_end"]),
                      key=lambda row: row["business_date"])
        require(len(days) == 14, f"{account_id}: two complete calendar windows required")
        prior = days[:7]
        current = days[7:]
        prior_spend = sum(cents(row["spend_usd"]) for row in prior)
        current_spend = None if any(row["spend_usd"] == "" for row in current) else sum(cents(row["spend_usd"]) for row in current)
        require(prior_spend == cents(expectation["prior_spend"]), f"{account_id}: prior mismatch")
        require(current_spend == cents(expectation["current_spend"]), f"{account_id}: current mismatch")
        require(sum(cents(row["planned_spend_usd"]) for row in current) == cents(expectation["current_plan"]),
                f"{account_id}: plan mismatch")
        accounts.append({
            "id": account_id, "name": days[0]["account_name"], "owner": days[0]["owner"],
            "expected_route": expectation["next_classification"],
            "days": [{"date": row["business_date"], "spend_cents": cents(row["spend_usd"]),
                      "plan_cents": cents(row["planned_spend_usd"]), "state": row["data_state"],
                      "evidence": json.loads(row["evidence"])} for row in days],
        })
    events = {}
    for key in ("correct_atlas", "late_harbor"):
        expectation = expected["events"][key]
        documents = [json.loads(path.read_text()) for path in (fixture / "events" / key).glob("*.json")]
        require(len(documents) == 1, f"{key}: expected one delivery file")
        doc = documents[0]
        amount = sum(cents(row["spend_usd"]) for row in doc["rows"]
                     if row["account_id"] == expectation["account_id"])
        require(amount == cents(expectation["after"]), f"{key}: correction mismatch")
        baseline_period = next(a for a in accounts if a["id"] == expectation["account_id"])["days"][7:]
        require(sum(day["spend_cents"] or 0 for day in baseline_period[:-1]) + amount == cents(expectation["period_after"]),
                f"{key}: updated seven-day mismatch")
        events[key] = {"account_id": expectation["account_id"], "date": expectation["business_date"],
                       "spend_cents": amount, "partition": doc["partition"], "version": doc["version"]}
    output = {"verified_on": "2026-10-07", "scope": "Verified synthetic baseline; historical sample, not a live database",
              "periods": periods, "scale": manifest, "accounts": accounts, "events": events}
    destination = ROOT / "site/demo.json"
    destination.write_text(json.dumps(output, indent=2) + "\n")
    print(f"Reconciled {len(rows):,} account-days and four independent scenarios; wrote {destination}")


if __name__ == "__main__":
    build()
