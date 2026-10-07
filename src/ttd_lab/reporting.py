"""A shared, exact-money comparison for executive and CSV reports."""

import csv
import hashlib
import io
import json
import tempfile
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

RULE_VERSION = "decline-v1"
NEXT_CHECK = {
    "commercial_investigation": "Account owner: inspect active campaign constraints, pauses, budget settings, and delivery context; confirm the cause before considering client outreach.",
    "data_investigation": "Data reviewer: locate missing delivery or coverage, validate expected campaign keys, and rerun the comparison before making a commercial assessment.",
    "planned_change": "Account owner: confirm the agreed campaign flight schedule; no unexpected-decline escalation is supported.",
    "plan_context": "Account owner: confirm the changed budget and flight context before interpreting the spend movement.",
    "no_baseline": "Review lifecycle context; a zero prior baseline cannot support a percentage-decline comparison.",
    "no_decline_signal": "No action from this decline rule; other questions require separate evidence.",
}


def as_cents(value):
    if value is None or value == "":
        return None
    amount = Decimal(str(value))
    if not amount.is_finite() or amount < 0 or amount * 100 != (amount * 100).to_integral_value():
        raise ValueError("Report amounts must be nonnegative USD with cent precision")
    return int(amount * 100)


def build_report(rows, end_date, capacity=5):
    """Compare adjacent 7-day windows, suppressing incomplete account totals.

    The common cohort excludes an account from BOTH periods if either period is
    incomplete. Known partial spend is disclosed separately, never compared as
    a complete total. Rule comparisons use exact integer cross-products.
    """
    if capacity < 1:
        raise ValueError("Report capacity must be positive")
    end = date.fromisoformat(str(end_date))
    dates = [(end - timedelta(days=i)).isoformat() for i in range(13, -1, -1)]
    grouped = defaultdict(dict)
    for row in rows:
        day = str(row["business_date"])
        if not dates[0] <= day <= dates[-1]:
            continue
        identity = row["account_id"]
        if day in grouped[identity]:
            raise ValueError(f"Duplicate account-day: {identity} / {day}")
        spend, plan = as_cents(row["spend_usd"]), as_cents(row["planned_spend_usd"])
        state = row["data_state"]
        if plan is None or state not in {"complete", "inactive", "missing_delivery"}:
            raise ValueError(f"Invalid report state: {identity} / {day}")
        if (spend is None) != (state == "missing_delivery"):
            raise ValueError(f"Missing spend and coverage disagree: {identity} / {day}")
        if state == "inactive" and (spend != 0 or plan != 0):
            raise ValueError(f"Inactive account-day must have zero spend and plan: {identity}")
        evidence = row["evidence"]
        if isinstance(evidence, str):
            evidence = json.loads(evidence)
        grouped[identity][day] = {"date": day, "spend_cents": spend, "plan_cents": plan,
                                  "state": state, "evidence": evidence,
                                  "account_file_id": int(row["account_file_id"]),
                                  "name": row["account_name"], "owner": row["owner"]}
    if not grouped:
        raise ValueError("No accepted account-days in the requested period")
    accounts = []
    for identity, by_date in sorted(grouped.items()):
        if set(by_date) != set(dates):
            raise ValueError(f"{identity}: all 14 calendar dates are required")
        days = [by_date[day] for day in dates]
        missing = [day["date"] for day in days if day["spend_cents"] is None]
        totals = []
        for window in (days[:7], days[7:]):
            totals.append({"spend_cents": None if any(d["spend_cents"] is None for d in window)
                           else sum(d["spend_cents"] for d in window),
                           "known_spend_cents": sum(d["spend_cents"] or 0 for d in window),
                           "plan_cents": sum(d["plan_cents"] for d in window)})
        prior, current = totals
        delta = None if missing else current["spend_cents"] - prior["spend_cents"]
        route = "no_decline_signal"
        if missing:
            route = "data_investigation"
        elif prior["spend_cents"] == 0:
            route = "no_baseline"
        elif prior["plan_cents"] > 0 and current["plan_cents"] == 0:
            route = "planned_change"
        elif prior["plan_cents"] == 0 or current["plan_cents"] * 10 < prior["plan_cents"] * 9:
            route = "plan_context"
        elif (prior["spend_cents"] >= 5_000_000 and -delta >= 1_000_000
              and -delta * 5 >= prior["spend_cents"]
              and 10 * (prior["spend_cents"] * current["plan_cents"]
                        - current["spend_cents"] * prior["plan_cents"])
              >= prior["plan_cents"] * current["plan_cents"]):
            route = "commercial_investigation"
        references = {}
        for day in days:
            for item in day["evidence"]:
                ref = {"date": day["date"], **item, "account_file_id": day["account_file_id"]}
                references[json.dumps(ref, sort_keys=True)] = ref
        accounts.append({"id": identity, "name": days[-1]["name"], "owner": days[-1]["owner"],
                         "prior": prior, "current": current, "change_cents": delta,
                         "route": route, "missing_dates": missing,
                         "next_check": NEXT_CHECK[route], "evidence": list(references.values())})
    complete = [a for a in accounts if a["route"] != "data_investigation"]
    issues = [a for a in accounts if a["route"] == "data_investigation"]
    candidates = sorted((a for a in complete if a["route"] == "commercial_investigation"),
                        key=lambda a: (a["change_cents"], a["id"]))
    planned = [a for a in complete if a["route"] == "planned_change"]
    cohorts = []
    for route in sorted({a["route"] for a in complete}):
        members = [a for a in complete if a["route"] == route]
        cohorts.append({"route": route, "accounts": len(members),
                        "prior_spend_cents": sum(a["prior"]["spend_cents"] for a in members),
                        "current_spend_cents": sum(a["current"]["spend_cents"] for a in members),
                        "change_cents": sum(a["change_cents"] for a in members)})
    daily = []
    for i in range(7):
        daily.append({"prior_date": dates[i], "current_date": dates[i + 7],
                      "prior_spend_cents": sum(grouped[a["id"]][dates[i]]["spend_cents"] for a in complete),
                      "current_spend_cents": sum(grouped[a["id"]][dates[i + 7]]["spend_cents"] for a in complete)})
    prior_total = sum(a["prior"]["spend_cents"] for a in complete)
    current_total = sum(a["current"]["spend_cents"] for a in complete)
    report = {
        "rule_version": RULE_VERSION, "capacity": capacity,
        "periods": {"prior_start": dates[0], "prior_end": dates[6],
                    "current_start": dates[7], "current_end": dates[-1]},
        "scope": "Fictional USD spend; historical sample; latest accepted source restatements",
        "summary": {"total_accounts": len(accounts), "comparable_accounts": len(complete),
                    "excluded_accounts": len(issues), "prior_spend_cents": prior_total,
                    "current_spend_cents": current_total, "change_cents": current_total - prior_total,
                    "prior_plan_cents": sum(a["prior"]["plan_cents"] for a in complete),
                    "current_plan_cents": sum(a["current"]["plan_cents"] for a in complete),
                    "candidate_count": len(candidates), "queued_count": min(len(candidates), capacity),
                    "deferred_count": max(0, len(candidates) - capacity),
                    "candidate_decline_cents": sum(-a["change_cents"] for a in candidates),
                    "planned_count": len(planned),
                    "planned_change_cents": sum(a["change_cents"] for a in planned),
                    "excluded_prior_known_cents": sum(a["prior"]["known_spend_cents"] for a in issues),
                    "excluded_current_known_cents": sum(a["current"]["known_spend_cents"] for a in issues)},
        "route_counts": dict(sorted(Counter(a["route"] for a in accounts).items())),
        "cohorts": cohorts, "daily": daily, "queue": candidates[:capacity],
        "data_issues": issues, "planned_changes": planned, "accounts": accounts,
    }
    if sum(c["change_cents"] for c in cohorts) != report["summary"]["change_cents"]:
        raise ValueError("Cohort bridge failed reconciliation")
    report["snapshot_id"] = hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest()[:16]
    return report


def publish_report(report, destination):
    """Write a completed snapshot in one directory; failed builds keep the prior latest pointer.

    Static readers resolve latest.json once, then use that snapshot's JSON/CSV.
    Existing content-addressed snapshots remain available for inspection.
    """
    directory = Path(destination)
    snapshot = directory / report["snapshot_id"]
    directory.mkdir(parents=True, exist_ok=True)
    public = {key: value for key, value in report.items() if key != "accounts"}
    handle = io.StringIO(newline="")
    fields = ["account_id", "account_name", "owner", "prior_spend_usd", "current_spend_usd",
              "prior_plan_usd", "current_plan_usd", "change_usd", "route", "missing_dates", "next_check"]
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    dollars = lambda value: "" if value is None else f"{Decimal(value) / 100:.2f}"
    for account in report["accounts"]:
        writer.writerow(dict(zip(fields, [account["id"], account["name"], account["owner"],
            dollars(account["prior"]["spend_cents"]), dollars(account["current"]["spend_cents"]),
            dollars(account["prior"]["plan_cents"]), dollars(account["current"]["plan_cents"]),
            dollars(account["change_cents"]), account["route"], ";".join(account["missing_dates"]), account["next_check"]])))
    contents = {"report.json": json.dumps(public, indent=2, sort_keys=True) + "\n", "accounts.csv": handle.getvalue()}
    if snapshot.exists():
        if any((snapshot / name).read_bytes() != content.encode() for name, content in contents.items()):
            raise ValueError("Existing snapshot differs; refusing to rewrite published evidence")
    else:
        with tempfile.TemporaryDirectory(dir=directory, prefix=".building-") as temporary:
            candidate = Path(temporary) / "snapshot"
            candidate.mkdir()
            for name, content in contents.items():
                (candidate / name).write_bytes(content.encode())
            candidate.rename(snapshot)
    with tempfile.NamedTemporaryFile(mode="w", dir=directory, prefix=".latest-", delete=False) as pointer:
        pointer.write(json.dumps({"snapshot_id": report["snapshot_id"]}, indent=2) + "\n")
    Path(pointer.name).replace(directory / "latest.json")
    return report["snapshot_id"]
