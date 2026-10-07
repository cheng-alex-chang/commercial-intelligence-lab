# First-slice verification

Verified October 6, 2026 in the local project environment.

- Python 3.14.4; Psycopg 3.3.6; pytest 9.1.1.
- Official `postgres:17` image; running server reports PostgreSQL 17.11.
- Fixture generator: 10 accounts, 56 dates, 170 baseline JSON files.
- Standalone contract validation: passed.
- Main database: 170 accepted source files, 560 account-day rows, one missing account-day.
- Full suite: 20 passed in 1.27 seconds; no skipped PostgreSQL checks.
- Contract tests cover deterministic bytes, independent scenario totals, expected-key coverage, currency types/precision, budget overlaps, manifest gaps, coordinated removal, and duplicate JSON fields.
- Integration tests cover replay and reconciliation; missing versus zero versus inactive; correction and retained bytes; replay of an older accepted file; late arrival; conflicting versions; coordinated removal; and rollback after writes followed by successful retry.

The integration database is `ttd_lab_test`. It is separate from the user-facing baseline database `ttd_lab`. Corrections and retirement were exercised only in the test database during verification.

The working view uses latest accepted versions. Published snapshots, period classification, signal ranking, cutoff/freshness enforcement, review events, API, and BI are pending. The loader serializes source acceptance and changes a batch atomically; it does not yet reconcile abandoned runs after a process kill or database outage.

## Commercial scale revision — October 7, 2026

The default profile now has 1,000 fictional accounts, 5,000 campaigns, 56 dates, 279,960 delivery aggregate rows, and 56,000 account-day rows. The normal-day target is $36,712,328.76, calibrated from the rounded public 2025 gross-spend reference of $13.4 billion / 365. Actual seed-42 baseline spend is $2,047,582,442.77 and implied paid impressions total 338,991,332,198. The original small lab remains in `ttd_lab`; the new dataset is in `ttd_lab_scale`.

All 23 tests passed, including eight PostgreSQL integration checks. The expanded checks cover financial target conservation, exact multi-campaign monetary aggregation, channel-specific synthetic CPM arithmetic, and multi-campaign SQL joins/corrections. Existing replay, missing/zero, deletion, rollback, and recovery checks now use enterprise monetary amounts in the compact test profile.

The complete commercial CSV reconciles to the generator's exact spend and paid impression totals, all four independent seven-day scenario expectations, and one missing account-day.

Measured on this local environment, in single runs rather than a controlled benchmark:

| Operation | Elapsed time |
| --- | --- |
| Source contract validation, full default | 1.146 seconds |
| Initial PostgreSQL load, 170 files / 279,960 delivery rows | 3.467 seconds |
| Count of accepted delivery rows | 0.084 seconds |
| Full account-day query after SQL adjustment, 56,000 rows | 3.086 seconds |

The larger profile exposed repeated JSON key expansion in the original SQL plan. Materializing expanded coverage keys and budgets before the join reduced this work. These timings do not establish event-level ingestion rate, concurrent throughput, or TTD production performance. Larger stress commands are available but have not been benchmarked.

## Public walkthrough — October 7, 2026

The site sample builder reconciles all 56,000 exported account-days to the scale manifest (exact spend and paid impressions), confirms one missing account-day, verifies both seven-day windows for four accounts against independent expectations, and verifies the correction/late-arrival files and updated period totals. It refuses a corrected export in place of the baseline. The committed sample is reproduced in CI before deployment.

Browser checks passed for all four cases: Atlas's sample correction changes current spend to $1.30M; Harbor remains unknown until the late sample arrives, then becomes $2.80M; Maple shows observed zero; Beacon shows a scheduled ending with no current plan. Mobile layout was inspected at a 390 × 844 viewport override with no horizontal page overflow. Browser console contained no warnings or errors. The walkthrough is static; event acceptance is illustrative and has no database side effect.

The updated plan removes mandatory model layers and tool branches. Python ingestion, PostgreSQL source history and SQL views, and a concise report are the core. Extra tools require a concrete learning or consumer need.
