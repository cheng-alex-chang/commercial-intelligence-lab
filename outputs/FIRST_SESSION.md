# First session: trustworthy commercial data

The first foundation is running in `/Users/alexchang/Downloads/ttd-onboarding`. All data and entities are fictional.

**Built and verified:** decision brief, four source contracts, deterministic Python generator, PostgreSQL loader, raw file history, replay/correction rules, failed-run ledger, and account-day SQL view. The fixtures have 1,000 fictional accounts, 5,000 campaigns, 56 dates, and 170 baseline files. The scaled view contains 56,000 account-day rows. See [the scale explanation](SCALE_OVERVIEW.md) for public reference values and synthetic assumptions.

## Read the evidence

The main database currently contains the baseline. On August 31, 2026:

| Account | Observed spend | Planned spend | Data state | Interpretation to discuss |
| --- | --- | --- | --- | --- |
| Atlas Retail | $150,000 | $500,000 | Complete | Reduced delivery needs comparison and context |
| Beacon Travel | $0 | $0 | Inactive | Flight ended on schedule |
| Harbor Foods | Unknown | $500,000 | Missing delivery | Investigate data before making a commercial claim |
| Maple Goods | $0 | $500,000 | Complete | A genuine observed zero, eligible for further investigation |

These are learning interpretations. The signal classifier and daily queue have not been implemented yet.

## Your first 30-minute walkthrough

1. Read [the decision brief](../docs/DECISION_BRIEF.md). Explain who acts and what decision the output supports.
2. Read [the source contracts](../docs/SOURCE_CONTRACTS.md). Identify the grain of each input and the scope of a corrected delivery file.
3. Open [the baseline account-day export](account_day_working.csv). Compare the four accounts above. Empty spend means unknown; numeric zero means observed zero or a documented inactive day.
4. Read [the SQL investigation queries](../sql/investigate.sql). Notice why a period total must check completeness before using SUM, which otherwise ignores NULL.
5. Replay the baseline and observe the loader's counts:

```sh
cd /Users/alexchang/Downloads/ttd-onboarding
.venv/bin/ttd-lab load data/fixtures-commercial/baseline
```

Expected: zero accepted files and 170 replayed files. Existing totals stay unchanged.

Then explain this in your own words: **why would treating Harbor's missing file as zero lead to a bad account recommendation?**

## Next build

Create two adjacent seven-day comparisons ending August 31, enforce eligibility, generate account priorities with evidence and next actions, and introduce a validated publication boundary. The independent baseline expectations are Atlas $2.8 million → $1.05 million, Beacon $2.8 million → $0, Harbor $2.8 million → unknown, and Maple $2.8 million → $0.

The local database is running on `127.0.0.1:55432`. Stop it with `docker compose stop` when finished; the project volume retains the data.
