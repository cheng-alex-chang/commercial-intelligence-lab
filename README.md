# TTD Commercial Intelligence Lab

A fictional preparation project for commercial intelligence engineering and analysis. Python, SQL, and PostgreSQL are the first stack. The revised [plan](PROJECT_PLAN.md) and [review](docs/PLAN_REVIEW.md) are preserved; the [original plan](docs/ORIGINAL_PROJECT_PLAN.md) is unchanged.

## First slice

M0 is implemented as a [decision brief](docs/DECISION_BRIEF.md), four [source contracts](docs/SOURCE_CONTRACTS.md), and independent [scenario expectations](tests/scenario_expectations.json). M1 adds deterministic source fixtures, atomic PostgreSQL ingestion, raw history, replay/version checks, a failed-run ledger, and an account-day working view.

The fixtures contain 10 accounts over 56 dates, ending August 31, 2026. They distinguish unexpected decline, planned campaign ending, missing delivery, and observed zero. Additional files exercise corrections, late arrival, and coordinated row removal. Every amount and identity is fictional.

**Verified October 6, 2026:** all 20 tests pass, including seven PostgreSQL integration checks. The main database is loaded with the baseline; correction exercises have been tested in the separate test database. Begin with [the first learning session](outputs/FIRST_SESSION.md).

This slice provides a working analytical view. The investigation queue, period classification, immutable publication snapshots, freshness gates, and review workflow are the next milestone.

## Run locally

From this project folder, create an isolated Python environment and start the local PostgreSQL container:

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
docker compose up -d --wait
.venv/bin/ttd-lab generate
.venv/bin/ttd-lab validate data/fixtures/baseline
.venv/bin/ttd-lab init-db
.venv/bin/ttd-lab load data/fixtures/baseline
.venv/bin/ttd-lab export
```

The database binds only to `127.0.0.1:55432`. The default development connection uses database/user `ttd_lab` and fictional local password `ttd_lab_local`. Override with `LAB_DATABASE_URL` if needed; `.env.example` documents the setting but the CLI does not automatically read `.env`.

Without database access, generation and contract validation still run:

```sh
PYTHONPATH=src python3 -m ttd_lab.cli generate
PYTHONPATH=src python3 -m ttd_lab.cli validate data/fixtures/baseline
python3 -m pytest -m 'not integration'
```

The CSV output is `outputs/account_day_working.csv`. Empty spend means unknown; an observed zero is numeric zero. Source evidence links to file IDs and versions in PostgreSQL. The reviewed SQL lives in [schema.sql](src/ttd_lab/schema.sql); example investigation queries are in [sql/investigate.sql](sql/investigate.sql).

## Walk through the failures

Run the baseline again: all 170 files replay without duplicating accepted records. Then accept a correction and the late file:

```sh
.venv/bin/ttd-lab load data/fixtures/baseline
.venv/bin/ttd-lab load data/fixtures/events/correct_atlas
.venv/bin/ttd-lab load data/fixtures/events/late_harbor
.venv/bin/ttd-lab export --output outputs/account_day_after_events.csv
```

Atlas's August 31 spend changes from $150 to $400, retaining both raw versions. Harbor's August 31 spend changes from unknown to $400. Replaying an accepted old version does not revert a newer one. To explore valid removal separately:

```sh
.venv/bin/ttd-lab load data/fixtures/events/retire_atlas
```

This replaces budgets, coverage, and the final display partition together, retiring Atlas's final-day campaign key. Replaying the baseline after these events leaves the newer accepted state intact. Start a new disposable database if you need a completely fresh baseline. Stop the container with `docker compose stop`; its volume retains the data.

## Tests

Contract tests run without PostgreSQL. Integration tests use a separate dedicated database and cover replay, reconciliation, missing versus zero, correction history, same-version conflicts, late arrival, deletion, rollback, and retry.

```sh
.venv/bin/python -m pytest -m 'not integration'
docker compose exec -T postgres createdb -U ttd_lab ttd_lab_test
LAB_TEST_DATABASE_URL=postgresql://ttd_lab:ttd_lab_local@127.0.0.1:55432/ttd_lab_test .venv/bin/python -m pytest
```

Create the test database once; subsequent test runs reuse it. Tests reset only its `lab` schema. They will not run without an explicit local `ttd_lab_test` connection. PostgreSQL integration checks must pass before calling M1 verified.

## Learning exercise

Read the decision brief, then compare Atlas, Beacon, Harbor, and Maple on August 31. Explain what you can conclude from each account's data and what remains unknown. Next, build the seven-day eligibility comparison and daily investigation queue on this foundation.
