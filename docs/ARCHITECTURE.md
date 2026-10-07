# A small system with evidence

The first useful output is an account investigation, backed by delivery, budget, and completeness evidence. The architecture follows that decision.

```text
Four fictional file contracts
           |
Python: validate and accept a batch atomically
           |
PostgreSQL: source history + accepted pointers + SQL views
           |
Account-day data -> shared comparisons -> executive website + CSV

Verified sample export -> static GitHub Pages walkthrough
```

## What exists

The database has three stored tables: `raw_files` preserves exact source bytes, parsed JSON, checksum, and version; `current_files` identifies the accepted version for each partition; `ingestion_runs` records success, replay, or failure. The loader validates the resulting combined source state before changing pointers. Accepted changes occur in one transaction. Failed attempts leave a run record.

Source-specific views extract typed account, budget, coverage, and delivery records. `account_day_working` aggregates at account × date before joining measures. It returns unknown spend when an expected delivery partition is absent, numeric zero when complete delivery explicitly reports zero, and inactive zero when no campaign is expected. All views and stored tables live in the same PostgreSQL `lab` schema.

These views express source grain and business logic without storing repeated bronze/silver/gold copies. Source history is retained because corrections and replay need evidence. It is useful functionality, rather than a requirement to adopt a medallion architecture.

`scripts/build_demo.py` checks the full baseline CSV against the generator's scale manifest and independent scenario expectations, then extracts four accounts and two source events into `site/demo.json`. The site reads that committed sample. Its event controls simulate acceptance in the browser; they do not change a database. A separate executive briefing applies the shared Python classifier to all accounts and publishes ranked priorities. Persistent review tracking remains future work.

## Why these tools

| Tool | Job | Reason to keep it |
| --- | --- | --- |
| Python + Psycopg | Fixtures, contracts, transactional ingestion, export | One language for data work and operational checks |
| PostgreSQL 17 + SQL | Source evidence and account-day analysis | Exact money, transactions, query inspection, one local dependency |
| Docker Compose | Start PostgreSQL reproducibly | One container; no orchestration cluster |
| pytest + GitHub Actions | Business correctness and repeatable verification | Replay, missing/zero, corrections, rollback, and reconciliation checks |
| HTML/CSS/JavaScript + GitHub Pages | Public walkthrough | Static files; no server, framework, or package build |

## Next increment

The executive report now uses complete-period comparisons, transparent routing, a portfolio bridge, and shared website/CSV output. Next, add operational freshness/cutoff handling and a short decision memo. Include account owner, observation, completeness, source versions, uncertainty, and next check. Publish only a successfully verified report, retaining the previous artifact if generation fails. Start with a manual batch command and documented freshness; add scheduling when cadence actually needs it.

Only expand when there is a concrete need: dbt for a difficult SQL dependency graph, Snowflake for a specific warehouse learning exercise, Tableau for an analyst handoff, an API for a live consumer, and an LLM for an independently evaluated question interface. None is a core dependency.

## Limits to explain

- The source history is append-only through the loader, not protected against a privileged user changing database records.
- The working view shows latest accepted restatements, not an immutable historical publication or the information known on a past date.
- Source acceptance is atomic. Ingestion process-kill recovery, operational cutoff enforcement, scheduling, and review persistence are pending. Report publication preserves immutable snapshots and advances a pointer only after files are complete.
- Financial quantities are calibrated to a public annual spend reference. Local aggregate processing does not establish TTD event throughput.

See [verification](VERIFICATION.md), [contracts](SOURCE_CONTRACTS.md), and the [scale explanation](../outputs/SCALE_OVERVIEW.md) for concrete evidence.
