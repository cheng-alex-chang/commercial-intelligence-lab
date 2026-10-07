import copy
import csv
import json
from datetime import date, timedelta
from decimal import Decimal

import pytest

from ttd_lab.reporting import build_report, publish_report


def account_rows(identity, current, prior="400000.00", plan="500000.00"):
    rows = []
    for index in range(14):
        rows.append({"account_id": identity, "account_name": identity.title(), "owner": f"owner-{identity}",
                     "business_date": date(2026, 8, 18) + timedelta(days=index),
                     "spend_usd": Decimal(prior if index < 7 else current),
                     "planned_spend_usd": Decimal(plan), "data_state": "complete",
                     "account_file_id": 1, "evidence": [{"partition": f"2026-08-{18+index}:display",
                         "delivery_file_id": 10+index, "delivery_version": 1,
                         "budget_file_id": 2, "coverage_file_id": 3}]})
    return rows


def test_independent_routes_comparable_cohort_and_exact_bridge():
    rows = account_rows("atlas", "150000.00") + account_rows("maple", "0.00")
    beacon = account_rows("beacon", "0.00")
    for row in beacon[7:]:
        row.update(planned_spend_usd=Decimal(0), data_state="inactive")
    harbor = account_rows("harbor", "400000.00")
    harbor[-1].update(spend_usd=None, data_state="missing_delivery")
    report = build_report(rows + beacon + harbor, "2026-08-31")
    assert {a["id"]: a["route"] for a in report["accounts"]} == {
        "atlas": "commercial_investigation", "maple": "commercial_investigation",
        "beacon": "planned_change", "harbor": "data_investigation"}
    assert [a["id"] for a in report["queue"]] == ["maple", "atlas"]
    summary = report["summary"]
    assert (summary["prior_spend_cents"], summary["current_spend_cents"], summary["change_cents"]) == (840000000, 105000000, -735000000)
    assert summary["candidate_decline_cents"] == 455000000
    assert summary["excluded_current_known_cents"] == 240000000
    assert report["data_issues"][0]["current"]["spend_cents"] is None
    assert sum(c["change_cents"] for c in report["cohorts"]) == -735000000
    assert sum(d["current_spend_cents"] for d in report["daily"]) == 105000000


def test_missing_prior_and_observed_zero_do_not_become_comparable():
    rows = account_rows("unknown", "0.00")
    rows[0].update(spend_usd=None, data_state="missing_delivery")
    report = build_report(rows, "2026-08-31")
    assert report["accounts"][0]["prior"]["spend_cents"] is None
    assert report["accounts"][0]["current"]["spend_cents"] == 0
    assert report["accounts"][0]["change_cents"] is None
    assert report["summary"]["comparable_accounts"] == 0
    assert report["queue"] == []


def test_reduced_plan_and_zero_baseline_are_routed_for_context():
    changed = account_rows("changed", "150000.00")
    for row in changed[7:]:
        row["planned_spend_usd"] = Decimal("200000.00")
    new = account_rows("new", "150000.00", prior="0.00")
    report = build_report(changed + new, "2026-08-31")
    assert {a["id"]: a["route"] for a in report["accounts"]} == {"changed": "plan_context", "new": "no_baseline"}
    assert report["queue"] == []


def test_pacing_boundary_is_exact_even_for_repeating_ratios():
    # 2/15 minus 1/30 is exactly 0.10, regardless of ratio rounding precision.
    rows = account_rows("boundary", "20000.00", prior="80000.00", plan="600000.00")
    report = build_report(rows, "2026-08-31")
    assert report["accounts"][0]["route"] == "commercial_investigation"


def test_capacity_is_deterministic_and_discloses_deferred_accounts():
    rows = account_rows("zeta", "0.00") + account_rows("alpha", "0.00")
    report = build_report(rows, "2026-08-31", capacity=1)
    assert [a["id"] for a in report["queue"]] == ["alpha"]
    assert report["summary"]["candidate_count"] == 2
    assert report["summary"]["deferred_count"] == 1
    assert build_report(list(reversed(rows)), "2026-08-31", capacity=1)["snapshot_id"] == report["snapshot_id"]


def test_invalid_source_shape_blocks_report():
    rows = account_rows("atlas", "150000.00")
    with pytest.raises(ValueError, match="all 14"):
        build_report(rows[:-1], "2026-08-31")
    with pytest.raises(ValueError, match="Duplicate"):
        build_report(rows + rows[:1], "2026-08-31")
    bad = copy.deepcopy(rows)
    bad[-1]["spend_usd"] = None
    with pytest.raises(ValueError, match="coverage disagree"):
        build_report(bad, "2026-08-31")
    bad[-1]["spend_usd"] = Decimal("1.001")
    with pytest.raises(ValueError, match="cent precision"):
        build_report(bad, "2026-08-31")


def test_failed_publication_retains_previous_snapshot_and_csv_reconciles(tmp_path, monkeypatch):
    from pathlib import Path

    original = build_report(account_rows("atlas", "150000.00"), "2026-08-31")
    snapshot = publish_report(original, tmp_path)
    assert publish_report(original, tmp_path) == snapshot
    with (tmp_path / snapshot / "accounts.csv").open(newline="") as handle:
        exported = list(csv.DictReader(handle))
    assert exported[0]["current_spend_usd"] == "1050000.00"
    assert exported[0]["change_usd"] == "-1750000.00"
    revised = build_report(account_rows("atlas", "400000.00"), "2026-08-31")
    rename = Path.rename

    def interrupted(path, target):
        if path.name == "snapshot":
            raise OSError("Injected publication failure")
        return rename(path, target)

    monkeypatch.setattr(Path, "rename", interrupted)
    with pytest.raises(OSError, match="Injected"):
        publish_report(revised, tmp_path)
    assert json.loads((tmp_path / "latest.json").read_text())["snapshot_id"] == snapshot
    assert not (tmp_path / revised["snapshot_id"]).exists()
    monkeypatch.setattr(Path, "rename", rename)
    new_snapshot = publish_report(revised, tmp_path)
    assert new_snapshot != snapshot
    assert (tmp_path / snapshot / "report.json").exists()
