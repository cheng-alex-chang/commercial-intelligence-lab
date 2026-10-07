"""Deterministic enterprise-scale aggregate inputs, with a small test profile."""

import json
import random
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

ANNUAL_SPEND_REFERENCE_USD = 13_400_000_000
DAILY_SPEND_REFERENCE_CENTS = ANNUAL_SPEND_REFERENCE_USD * 100 // 365
FINANCIAL_SOURCE = "https://investors.thetradedesk.com/news-and-events/news/news-details/2026/The-Trade-Desk-Reports-Fourth-Quarter-and-Fiscal-Year-2025-Financial-Results/default.aspx"
CPM_CENTS = {"display": 400, "ctv": 2500, "audio": 1200}  # Fictional effective CPMs.


def dollars(cents):
    return f"{cents // 100}.{cents % 100:02d}"


def impressions(cents, channel):
    return cents * 1000 // CPM_CENTS[channel]


def split_cents(total, count, index):
    quotient, remainder = divmod(total, count)
    return quotient + (index < remainder)


def envelope(source, rows, partition="all", version=1):
    return {"schema_version": 1, "source": source, "partition": partition,
            "version": version, "rows": rows}


def save(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text() != content:
        raise ValueError(f"Refusing to overwrite different fixture bytes: {path}")
    path.write_text(content)


def generate(destination: Path, seed=42, profile="commercial", account_count=None,
             campaigns_per_account=None, days=56):
    if profile not in {"commercial", "unit"}:
        raise ValueError("Profile must be commercial or unit")
    account_count = account_count if account_count is not None else (1000 if profile == "commercial" else 10)
    campaigns_per_account = campaigns_per_account if campaigns_per_account is not None else (5 if profile == "commercial" else 1)
    if not 10 <= account_count <= 100_000 or not 1 <= campaigns_per_account <= 100 or not 14 <= days <= 3650:
        raise ValueError("Use 10–100000 accounts, 1–100 campaigns per account, and 14–3650 days")
    if profile == "unit" and (account_count, campaigns_per_account, days) != (10, 1, 56):
        raise ValueError("The unit profile is fixed at 10 accounts, one campaign each, and 56 days")
    rng = random.Random(seed)
    end = date(2026, 8, 31)
    dates = [end - timedelta(days=days - 1 - i) for i in range(days)]
    names = [("atlas", "Atlas Retail"), ("beacon", "Beacon Travel"),
             ("harbor", "Harbor Foods"), ("maple", "Maple Goods"),
             ("cedar", "Cedar Auto"), ("dune", "Dune Outdoors"),
             ("elm", "Elm Home"), ("fern", "Fern Fashion"),
             ("grove", "Grove Tech"), ("ivy", "Ivy Books")]
    names += [(f"account-{i:05d}", f"Fictional Account {i:05d}") for i in range(10, account_count)]
    accounts = [{"account_id": key, "account_name": name, "owner": f"owner-{i % 50 + 1}",
                 "agency": f"agency-{i % 25 + 1}", "segment": "enterprise" if i < 4 else "mixed"}
                for i, (key, name) in enumerate(names)]
    # Four control accounts represent large fictional commercial portfolios.
    spend = {key: 40_000_000 for key, _ in names[:4]}  # $400,000/account/day.
    if profile == "commercial":
        weights = [rng.lognormvariate(0, 1.5) for _ in names[4:]]
        remaining = DAILY_SPEND_REFERENCE_CENTS - sum(spend.values())
        total_weight = sum(weights)
        allocations = [int(remaining * weight / total_weight) for weight in weights]
        allocations[-1] += remaining - sum(allocations)
        spend.update({key: value for (key, _), value in zip(names[4:], allocations)})
    else:
        spend.update({key: 40_000_000 for key, _ in names[4:]})
    budgets = []
    campaign_index = {}
    for key, _ in names:
        for index in range(campaigns_per_account):
            channel = ("ctv" if key == "beacon" else "audio" if key == "harbor" else
                       "display" if key in {"atlas", "maple"} else
                       ("ctv" if index % 2 else "display"))
            campaign_id = f"campaign-{key}" if campaigns_per_account == 1 else f"campaign-{key}-{index:03d}"
            campaign_index[campaign_id] = index
            budgets.append({"campaign_id": campaign_id, "account_id": key, "channel": channel,
                            "effective_from": dates[0].isoformat(), "effective_to": end.isoformat(),
                            "flight_start": dates[0].isoformat(),
                            "flight_end": (end - timedelta(days=7) if key == "beacon" else end).isoformat(),
                            "planned_daily_spend_usd": dollars(split_cents(spend[key] * 5 // 4, campaigns_per_account, index))})
    by_channel = {channel: [b for b in budgets if b["channel"] == channel] for channel in CPM_CENTS}
    baseline = destination / "baseline"
    coverage = []
    final_deliveries = {}
    total_cents = total_impressions = delivery_rows = 0
    for business_day in dates:
        daily_spend = dict(spend)
        for key, _ in names[4:]:
            # Vary ordinary accounts by +/-5%; fixture controls are exact.
            daily_spend[key] = spend[key] * rng.randint(9500, 10500) // 10000
        if business_day > end - timedelta(days=7):
            daily_spend["atlas"] = 15_000_000
            daily_spend["maple"] = 0
        for channel, channel_budgets in by_channel.items():
            active = [b for b in channel_budgets if business_day.isoformat() <= b["flight_end"]]
            keys = [{"campaign_id": b["campaign_id"], "account_id": b["account_id"]} for b in active]
            coverage.append({"business_date": business_day.isoformat(), "channel": channel, "expected_keys": keys})
            rows = []
            for budget in active:
                key = budget["account_id"]
                cents = split_cents(daily_spend[key], campaigns_per_account, campaign_index[budget["campaign_id"]])
                rows.append({"campaign_id": budget["campaign_id"], "account_id": key,
                             "spend_usd": dollars(cents), "impressions": impressions(cents, channel)})
            partition = f"{business_day}:{channel}"
            payload = envelope("delivery", rows, partition)
            if business_day == end:
                final_deliveries[channel] = payload
            if not (business_day == end and channel == "audio"):
                save(baseline / "delivery" / f"{business_day}_{channel}_v1.json", payload)
                delivery_rows += len(rows)
                total_cents += sum(int(Decimal(row["spend_usd"]) * 100) for row in rows)
                total_impressions += sum(row["impressions"] for row in rows)
    save(baseline / "accounts_v1.json", envelope("accounts", accounts))
    save(baseline / "budgets_v1.json", envelope("budgets", budgets))
    save(baseline / "coverage_v1.json", envelope("coverage", coverage))
    corrected = deepcopy(final_deliveries["display"])
    corrected["version"] = 2
    for row in corrected["rows"]:
        if row["account_id"] == "atlas":
            cents = split_cents(spend["atlas"], campaigns_per_account, campaign_index[row["campaign_id"]])
            row.update(spend_usd=dollars(cents), impressions=impressions(cents, "display"))
    save(destination / "events" / "correct_atlas" / f"{end}_display_v2.json", corrected)
    save(destination / "events" / "late_harbor" / f"{end}_audio_v1.json", final_deliveries["audio"])
    retired_budgets = deepcopy(budgets)
    for budget in retired_budgets:
        if budget["account_id"] == "atlas":
            budget["flight_end"] = (end - timedelta(days=1)).isoformat()
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
    summary = {"profile": profile, "baseline_files": len(list(baseline.rglob("*.json"))),
               "accounts": len(accounts), "campaigns": len(budgets), "business_dates": len(dates),
               "delivery_rows": delivery_rows, "account_day_rows": len(accounts) * len(dates),
               "seed": seed, "baseline_spend_usd": dollars(total_cents),
               "baseline_paid_impressions": total_impressions,
               "calibrated_normal_day_spend_usd": dollars(sum(spend.values())),
               "scale_reference": {"year": 2025, "reported_gross_spend_usd": ANNUAL_SPEND_REFERENCE_USD,
                                   "annual_average_daily_gross_spend_usd": dollars(DAILY_SPEND_REFERENCE_CENTS),
                                   "source_url": FINANCIAL_SOURCE},
               "scope": "Synthetic daily campaign aggregates; financial scale proxy, not TTD event throughput or actual accounts",
               "fictional_cpm_usd": {channel: dollars(cents) for channel, cents in CPM_CENTS.items()}}
    save(destination / "scale_manifest.json", summary)
    return summary
