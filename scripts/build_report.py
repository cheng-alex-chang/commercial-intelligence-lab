"""Reproduce the public historical executive briefing from the full verified CSV."""

import csv
from pathlib import Path

from ttd_lab.reporting import build_report, publish_report

ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    with (ROOT / "outputs/account_day_working.csv").open(newline="") as handle:
        report = build_report(list(csv.DictReader(handle)), "2026-08-31")
    snapshot = publish_report(report, ROOT / "site/reports")
    print(f"Published executive sample {snapshot}: {report['summary']}")
