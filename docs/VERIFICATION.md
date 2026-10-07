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
