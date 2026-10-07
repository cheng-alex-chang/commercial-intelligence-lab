"""Deterministic inputs. Expected results live independently in tests/."""

import json
import random
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path


def envelope(source, rows, partition="all", version=1):
    return {"schema_version": 1, "source": source, "partition": partition,
            "version": version, "rows": rows}


def save(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text() != content:
        raise ValueError(f"Refusing to overwrite different fixture bytes: {path}")
    path.write_text(content)


def generate(destination: Path, seed=42):
    rng = random.Random(seed)
    end = date(2026, 8, 31)
    dates = [end - timedelta(days=55 - i) for i in range(56)]
    names = [("atlas", "Atlas Retail"), ("beacon", "Beacon Travel"),
             ("harbor", "Harbor Foods"), ("maple", "Maple Goods"),
             ("cedar", "Cedar Auto"), ("dune", "Dune Outdoors"),
             ("elm", "Elm Home"), ("fern", "Fern Fashion"),
             ("grove", "Grove Tech"), ("ivy", "Ivy Books")]
    accounts = [{"account_id": key, "account_name": name, "owner": f"owner-{i % 3 + 1}",
                 "agency": f"agency-{i % 2 + 1}", "segment": "mid-market"}
                for i, (key, name) in enumerate(names)]
    budgets = [{"campaign_id": f"campaign-{key}", "account_id": key,
                "channel": "ctv" if key == "beacon" else "audio" if key == "harbor" else "display",
                "effective_from": dates[0].isoformat(), "effective_to": end.isoformat(),
                "flight_start": dates[0].isoformat(),
                "flight_end": (end - timedelta(days=7) if key == "beacon" else end).isoformat(),
                "planned_daily_spend_usd": "500.00"} for key, _ in names]
    baseline = destination / "baseline"
    coverage = []
    deliveries = {}
    for day in dates:
        for channel in ("audio", "ctv", "display"):
            active = [b for b in budgets if b["channel"] == channel and day.isoformat() <= b["flight_end"]]
            keys = [{"campaign_id": b["campaign_id"], "account_id": b["account_id"]} for b in active]
            coverage.append({"business_date": day.isoformat(), "channel": channel, "expected_keys": keys})
            rows = []
            for budget in active:
                key = budget["account_id"]
                cents = 40000
                if day > end - timedelta(days=7) and key == "atlas":
                    cents = 15000
                elif day > end - timedelta(days=7) and key == "maple":
                    cents = 0
                elif key not in {"atlas", "beacon", "harbor", "maple"}:
                    cents += rng.randint(-2000, 2000)
                rows.append({"campaign_id": budget["campaign_id"], "account_id": key,
                             "spend_usd": f"{cents // 100}.{cents % 100:02d}", "impressions": cents * 2})
            partition = f"{day}:{channel}"
            payload = envelope("delivery", rows, partition)
            deliveries[partition] = payload
            if not (day == end and channel == "audio"):
                save(baseline / "delivery" / f"{day}_{channel}_v1.json", payload)
    save(baseline / "accounts_v1.json", envelope("accounts", accounts))
    save(baseline / "budgets_v1.json", envelope("budgets", budgets))
    save(baseline / "coverage_v1.json", envelope("coverage", coverage))
    corrected = deepcopy(deliveries[f"{end}:display"])
    corrected["version"] = 2
    for row in corrected["rows"]:
        if row["account_id"] == "atlas":
            row.update(spend_usd="400.00", impressions=80000)
    save(destination / "events" / "correct_atlas" / f"{end}_display_v2.json", corrected)
    save(destination / "events" / "late_harbor" / f"{end}_audio_v1.json", deliveries[f"{end}:audio"])
    retired_budgets = deepcopy(budgets)
    retired_budgets[0]["flight_end"] = (end - timedelta(days=1)).isoformat()
    retired_coverage = deepcopy(coverage)
    for row in retired_coverage:
        if row["business_date"] == str(end) and row["channel"] == "display":
            row["expected_keys"] = [k for k in row["expected_keys"] if k["account_id"] != "atlas"]
    removed = deepcopy(corrected)
    removed["version"] = 3
    removed["rows"] = [r for r in removed["rows"] if r["account_id"] != "atlas"]
    retirement = destination / "events" / "retire_atlas"
    save(retirement / "budgets_v2.json", envelope("budgets", retired_budgets, version=2))
    save(retirement / "coverage_v2.json", envelope("coverage", retired_coverage, version=2))
    save(retirement / f"{end}_display_v3.json", removed)
    return {"baseline_files": len(list(baseline.rglob("*.json"))), "accounts": len(accounts),
            "business_dates": len(dates), "seed": seed}
