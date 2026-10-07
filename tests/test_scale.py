from decimal import Decimal

from ttd_lab.contracts import load_files, validate_state
from ttd_lab.fixtures import DAILY_SPEND_REFERENCE_CENTS, generate, split_cents


def test_commercial_calibration_and_multi_campaign_aggregation(tmp_path):
    summary = generate(tmp_path, profile="commercial", account_count=20, campaigns_per_account=3, days=14)
    docs = {(doc["source"], doc["partition"]): doc for _, _, doc in load_files(tmp_path / "baseline")}
    validate_state(docs)
    assert summary["accounts"] == 20
    assert summary["campaigns"] == 60
    assert summary["account_day_rows"] == 280
    assert summary["delivery_rows"] == 60 * 14 - 3 * 7 - 3
    assert Decimal(summary["calibrated_normal_day_spend_usd"]) * 100 == DAILY_SPEND_REFERENCE_CENTS
    # Exact enterprise control amounts survive a split with fractional cents.
    atlas = [r for r in docs[("delivery", "2026-08-31:display")]["rows"] if r["account_id"] == "atlas"]
    assert len(atlas) == 3
    assert sum(Decimal(r["spend_usd"]) for r in atlas) == Decimal("150000.00")
    assert sum(r["impressions"] for r in atlas) in range(37_500_000 - 3, 37_500_000 + 1)
    # Mixed channel effective CPMs are explicit synthetic assumptions.
    for channel, cpm in {"display": Decimal("4"), "ctv": Decimal("25"), "audio": Decimal("12")}.items():
        row = docs[("delivery", f"2026-08-18:{channel}")]["rows"][0]
        paid_impressions = Decimal(row["spend_usd"]) * 1000 / cpm
        assert Decimal(row["impressions"]) <= paid_impressions < row["impressions"] + 1


def test_campaign_split_conserves_money():
    assert sum(split_cents(40_000_000, 7, index) for index in range(7)) == 40_000_000
