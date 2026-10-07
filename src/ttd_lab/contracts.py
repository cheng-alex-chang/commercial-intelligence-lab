"""Validate the complete proposed accepted state before any database mutation."""

import json
import re
from datetime import date
from pathlib import Path

SOURCES = {"accounts", "budgets", "coverage", "delivery"}
CHANNELS = {"audio", "ctv", "display"}
FIELDS = {
    "accounts": {"account_id", "account_name", "owner", "agency", "segment"},
    "budgets": {"campaign_id", "account_id", "channel", "effective_from", "effective_to",
                "flight_start", "flight_end", "planned_daily_spend_usd"},
    "coverage": {"business_date", "channel", "expected_keys"},
    "delivery": {"campaign_id", "account_id", "spend_usd", "impressions"},
}


class ContractError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ContractError(message)


def strict_object(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, f"Duplicate JSON field: {key}")
        obj[key] = value
    return obj


def read_document(path: Path):
    raw = path.read_bytes()
    try:
        doc = json.loads(raw, object_pairs_hook=strict_object)
    except (ValueError, UnicodeError) as exc:
        raise ContractError(f"Invalid JSON in {path.name}: {exc}") from exc
    validate_document(doc)
    return raw, doc


def day(value):
    require(isinstance(value, str), "Date must be an ISO string")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ContractError(f"Invalid date: {value}") from exc
    require(parsed.isoformat() == value, "Date must use YYYY-MM-DD")
    return parsed


def amount(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9]{1,16}\.[0-9]{2}", value),
            "USD must be a nonnegative two-decimal string fitting NUMERIC(18,2)")


def pair(row):
    return row["campaign_id"], row["account_id"]


def validate_document(doc):
    require(isinstance(doc, dict), "Envelope must be an object")
    require(set(doc) == {"schema_version", "source", "partition", "version", "rows"}, "Invalid envelope fields")
    require(type(doc["schema_version"]) is int and doc["schema_version"] == 1, "Unsupported schema version")
    require(isinstance(doc["source"], str) and doc["source"] in SOURCES, "Unknown source")
    require(type(doc["version"]) is int and doc["version"] > 0, "Version must be a positive integer")
    require(isinstance(doc["partition"], str), "Partition must be a string")
    source = doc["source"]
    if source == "delivery":
        bits = doc["partition"].split(":")
        require(len(bits) == 2 and bits[1] in CHANNELS, "Invalid delivery partition")
        day(bits[0])
    else:
        require(doc["partition"] == "all", "Snapshot source must use all partition")
    require(isinstance(doc["rows"], list), "Rows must be an array")
    seen = set()
    for row in doc["rows"]:
        require(isinstance(row, dict) and set(row) == FIELDS[source], f"Invalid {source} row fields")
        for field, value in row.items():
            if field not in {"expected_keys", "impressions", "spend_usd", "planned_daily_spend_usd"}:
                require(isinstance(value, str) and bool(value.strip()), f"{field} must be nonempty text")
        if source == "accounts":
            key = row["account_id"]
        elif source == "budgets":
            require(row["channel"] in CHANNELS, "Unknown budget channel")
            require(day(row["effective_from"]) <= day(row["effective_to"]), "Invalid effective range")
            require(day(row["flight_start"]) <= day(row["flight_end"]), "Invalid flight range")
            amount(row["planned_daily_spend_usd"])
            key = row["campaign_id"], row["channel"], row["effective_from"]
        elif source == "coverage":
            day(row["business_date"])
            require(row["channel"] in CHANNELS, "Unknown coverage channel")
            require(isinstance(row["expected_keys"], list), "expected_keys must be an array")
            expected = set()
            for entry in row["expected_keys"]:
                require(isinstance(entry, dict) and set(entry) == {"campaign_id", "account_id"}, "Invalid expected key")
                require(all(isinstance(v, str) and v.strip() for v in entry.values()), "Expected IDs must be nonempty strings")
                require(entry["campaign_id"] not in expected, "Duplicate expected campaign")
                expected.add(entry["campaign_id"])
            key = row["business_date"], row["channel"]
        else:
            amount(row["spend_usd"])
            require(type(row["impressions"]) is int and 0 <= row["impressions"] <= 9223372036854775807,
                    "Impressions must be a nonnegative BIGINT integer")
            key = row["campaign_id"]
        require(key not in seen, f"Duplicate {source} row key: {key}")
        seen.add(key)


def validate_state(documents):
    for key, doc in documents.items():
        validate_document(doc)
        require(key == (doc["source"], doc["partition"]), "Document identity mismatch")
    for source in SOURCES - {"delivery"}:
        require((source, "all") in documents, f"Missing required {source} snapshot")
    accounts = {r["account_id"] for r in documents[("accounts", "all")]["rows"]}
    budgets = documents[("budgets", "all")]["rows"]
    require(accounts and budgets, "Accounts and budgets cannot be empty")
    owners = {}
    ranges = {}
    for row in budgets:
        require(row["account_id"] in accounts, "Budget references unknown account")
        campaign = row["campaign_id"]
        require(owners.setdefault(campaign, row["account_id"]) == row["account_id"], "Campaign ownership changed")
        key = campaign, row["channel"]
        interval = day(row["effective_from"]), day(row["effective_to"])
        for start, end in ranges.setdefault(key, []):
            require(interval[1] < start or interval[0] > end, "Overlapping budget effective ranges")
        ranges[key].append(interval)
    coverage = documents[("coverage", "all")]["rows"]
    require(coverage, "Coverage calendar cannot be empty")
    dates = sorted({day(r["business_date"]) for r in coverage})
    require(len(dates) == (dates[-1] - dates[0]).days + 1, "Coverage date calendar has a gap")
    channels = {b["channel"] for b in budgets}
    require({(r["business_date"], r["channel"]) for r in coverage} ==
            {(d.isoformat(), c) for d in dates for c in channels}, "Coverage partition calendar has a gap or extra channel")
    expected_partitions = {}
    for row in coverage:
        d = row["business_date"]
        expected = {pair(b) for b in budgets if b["channel"] == row["channel"] and
                    b["effective_from"] <= d <= b["effective_to"] and b["flight_start"] <= d <= b["flight_end"]}
        require({pair(k) for k in row["expected_keys"]} == expected, "Coverage keys disagree with active budget plan")
        expected_partitions[f"{d}:{row['channel']}"] = expected
    for (source, partition), doc in documents.items():
        if source == "delivery":
            require(partition in expected_partitions, "Delivery outside coverage calendar")
            require({pair(r) for r in doc["rows"]} == expected_partitions[partition],
                    f"Delivery keys disagree with expected coverage: {partition}")


def load_files(path):
    paths = [path] if path.is_file() else sorted(path.rglob("*.json"))
    require(paths, f"No JSON source files found: {path}")
    return [(p, *read_document(p)) for p in paths]
