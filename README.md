# Commercial Intelligence Lab

**A spend decline is a question. Start with evidence.**

A focused Python and SQL project for answering: **which accounts should an owner investigate today, and what evidence supports the next check?** It practices commercial analysis and reliable data handling using fictional accounts at a calibrated financial scale.

[![Verify and publish](https://github.com/cheng-alex-chang/commercial-intelligence-lab/actions/workflows/verify-and-publish.yml/badge.svg)](https://github.com/cheng-alex-chang/commercial-intelligence-lab/actions/workflows/verify-and-publish.yml)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-306998)
![PostgreSQL 17](https://img.shields.io/badge/PostgreSQL-17-4169e1)
![Data: synthetic](https://img.shields.io/badge/Data-synthetic-cc502c)

**[Explore the live walkthrough →](https://cheng-alex-chang.github.io/commercial-intelligence-lab/)** · [Architecture](docs/ARCHITECTURE.md) · [Verification](docs/VERIFICATION.md) · [Project plan](PROJECT_PLAN.md)

The walkthrough lets you inspect four account cases, accept a sample source correction or late file, and trace the daily values to their source versions. It uses a verified historical sample; browser controls do not change a database.

## Four cases to explain

Compare August 18–24 with August 25–31, 2026. Dollar amounts are fictional.

| Account | Prior spend | Current spend | Current plan | Evidence and next check |
| --- | ---: | ---: | ---: | --- |
| Atlas Retail | $2.80M | $1.05M | $3.50M | Complete evidence; stable plan. Inspect an unexpected delivery decline. |
| Beacon Travel | $2.80M | $0 | $0 | Flight ended as scheduled. Confirm the planned ending. |
| Harbor Foods | $2.80M | **Unknown** | $3.50M | Required delivery is missing. Locate the file before assessing a decline. |
| Maple Goods | $2.80M | **$0 observed** | $3.50M | Complete explicit zero rows. Check pause or delivery constraints. |

The scenario interpretations above are analytical examples, checked against independent expected totals. The automated daily classifier and ranked investigation queue are the next milestone. A spend decline alone does not establish churn risk, revenue loss, or a causal explanation.

## Architecture

```mermaid
flowchart LR
    A[Accounts · budgets · coverage · delivery] --> B[Python: validate and accept atomically]
    B --> C[PostgreSQL: source versions and SQL views]
    C --> D[Account-day CSV]
    D --> E[Investigation report: next milestone]
    D --> F[Verified sample → GitHub Pages]
```

One database holds three stored tables: source history, accepted-file pointers, and ingestion runs. Direct SQL views expose typed sources and account-day analysis. Exact source bytes and versions support replay, corrections, and investigation evidence. Grain and completeness checks protect business meaning.

| Tool | Purpose |
| --- | --- |
| Python + Psycopg | Deterministic fixtures, contracts, transactional ingestion, CSV export |
| PostgreSQL 17 + SQL | Exact monetary arithmetic, accepted source state, account-day queries |
| Docker Compose | One reproducible local database container |
| pytest + GitHub Actions | Contract/integration checks and verified site deployment |
| Plain HTML/CSS/JavaScript + GitHub Pages | Static interactive project walkthrough |

Extra platforms are optional learning exercises. Read the [architecture decisions and limits](docs/ARCHITECTURE.md).

## What is implemented

- Four file contracts with key, type, currency, date, replacement, and expected-coverage validation.
- Deterministic commercial and compact correctness profiles, with corrections and late-arrival events.
- Atomic source acceptance, checksum replay, version conflict rejection, and a failed-run ledger.
- Exact source history; accepting a newer file replaces its entire partition. Replaying an accepted older file cannot revert it.
- Account-day SQL that distinguishes missing delivery, explicit zero, and inactive campaigns, with source references.
- A reconciled CSV export, 23 passing tests including 8 PostgreSQL integration checks, and a reproducible public sample.

**Next:** two-period eligibility, a capacity-limited investigation report with owner/evidence/next check, successful-publication checks, and visible freshness. Persistent review events and production scheduling remain optional follow-ups.

## Scale, stated precisely

The default seed-42 dataset has **1,000 fictional accounts**, **5,000 campaigns**, **56 dates**, **279,960 delivery aggregates**, and **56,000 account-day rows**. Its known baseline spend totals **$2,047,582,442.77**.

Normal-day simulated spend is calibrated to approximately **$36.7M**, using TTD's reported **$13.4B 2025 gross spend ÷ 365** as a financial reference. The spend proxy is not a reconstruction of TTD accounting; account counts, campaign mix, CPMs, and dates are fictional. [TTD's financial results](https://investors.thetradedesk.com/news-and-events/news/news-details/2026/The-Trade-Desk-Reports-Fourth-Quarter-and-Fiscal-Year-2025-Financial-Results/default.aspx).

A campaign-day record can represent millions of paid impressions. This lab processes aggregates and does not demonstrate TTD's platform event throughput. Paid impressions and platform-analyzed inventory are different measures. See [scale assumptions and public sources](outputs/SCALE_OVERVIEW.md).

| Operation | Measured local time |
| --- | ---: |
| Full source validation | 1.146s |
| Initial load: 170 files / 279,960 delivery rows | 3.467s |
| Account-day query: 56,000 rows | 3.086s |

Single runs in one local environment, rather than a controlled benchmark. [Method and verification evidence](docs/VERIFICATION.md).

## Run locally

Requirements: Python 3.11+, Docker with Compose, and an available local port 55432. From a fresh clone:

```sh
git clone https://github.com/cheng-alex-chang/commercial-intelligence-lab.git
cd commercial-intelligence-lab
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
docker compose up -d --wait
.venv/bin/ttd-lab generate
.venv/bin/ttd-lab validate data/fixtures-commercial/baseline
.venv/bin/ttd-lab init-db
.venv/bin/ttd-lab load data/fixtures-commercial/baseline
.venv/bin/ttd-lab export
```

The CSV is `outputs/account_day_working.csv`. Empty spend means unknown; numeric zero means zero. Explore [the SQL investigation queries](sql/investigate.sql) and [first learning session](outputs/FIRST_SESSION.md).

PostgreSQL binds to `127.0.0.1:55432`. The local-only default URL is `postgresql://ttd_lab:ttd_lab_local@127.0.0.1:55432/ttd_lab_scale`; override with `LAB_DATABASE_URL`. The CLI does not read `.env` automatically. The password in Compose is a fictional local development value.

On an existing Docker volume, `POSTGRES_DB` does not create a newly named database. Create `ttd_lab_scale` once if absent using `docker compose exec -T postgres createdb -U ttd_lab ttd_lab_scale`. Fresh volumes create it automatically. The earlier small lab database is retained separately as `ttd_lab`.

### Walk through source events

```sh
# All 170 accepted files replay; no duplicate accepted records.
.venv/bin/ttd-lab load data/fixtures-commercial/baseline
# Atlas final-day spend changes from $150,000 to $400,000.
.venv/bin/ttd-lab load data/fixtures-commercial/events/correct_atlas
# Harbor final-day spend changes from unknown to $400,000.
.venv/bin/ttd-lab load data/fixtures-commercial/events/late_harbor
.venv/bin/ttd-lab export --output outputs/account_day_after_events.csv
```

Atlas's current period becomes $1.30M; Harbor's becomes $2.80M. History remains available. A separate `events/retire_atlas` exercise updates budget, expected coverage, and delivery together to remove final-day active keys. Replaying the baseline retains newer accepted versions; it does not restore a fresh baseline. Use a new disposable database for a separate dataset or fresh run. Stop with `docker compose stop` to retain data.

### Verify

```sh
# Checks that need no database:
.venv/bin/python -m pytest -m 'not integration'
# Create once; the integration suite resets only this database's lab schema.
docker compose exec -T postgres createdb -U ttd_lab ttd_lab_test
LAB_TEST_DATABASE_URL=postgresql://ttd_lab:ttd_lab_local@127.0.0.1:55432/ttd_lab_test .venv/bin/python -m pytest -q
```

Integration tests require the explicit local `ttd_lab_test` connection. They cover monetary reconciliation, multi-campaign joins, replay, conflicting versions, missing/zero/inactive states, correction history, late arrival, coordinated removal, rollback, and retry.

### Reproduce the site sample

After generating and exporting a **fresh baseline**:

```sh
.venv/bin/python scripts/build_demo.py
python3 -m http.server 8000 --directory site
```

Open [localhost:8000](http://localhost:8000). The builder reconciles the full export to the scale manifest and independently specified scenario totals before writing `site/demo.json`. It rejects corrected or incompatible exports. GitHub Actions repeats tests and baseline reproduction, then deploys the static site only after verification succeeds.

### Change row volume

```sh
.venv/bin/ttd-lab generate --profile unit
.venv/bin/ttd-lab generate --accounts 2000 --campaigns-per-account 10 --days 90 --output data/stress-2000
```

The unit profile has 10 accounts, retaining enterprise amounts for scenario checks. The stress example produces roughly 1.8M campaign-day records; it is not benchmarked. More accounts/campaigns repartition the same financial target. More dates increase history. Use a separate database for each differently sized dataset.

## Repository guide

```text
src/ttd_lab/        Generator, contracts, ingestion, CLI, SQL views
sql/               Queries to inspect coverage and period totals
tests/             Independent expectations and correctness checks
scripts/           Reconciled public sample builder
site/              Static GitHub Pages walkthrough and verified sample
docs/              Decision brief, contracts, architecture, verification
outputs/           Learning exercises and scale explanation
.github/workflows/ Verification and Pages publication
```

The [revised plan](PROJECT_PLAN.md) defines completion gates. The [original planning document](docs/ORIGINAL_PROJECT_PLAN.md) is archived unchanged as reference material; its broader proposed stack is superseded by the revised scope.

Built by Alex Chang as an independent preparation project. Not affiliated with The Trade Desk; no private TTD data or systems are used.
