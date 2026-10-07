# Core source contracts — version 1

These contracts define the fictional lab. JSON is used for the first implementation so typed envelope metadata and nested coverage keys travel with each daily file.

## Shared envelope and acceptance

Every file contains `schema_version: 1`, `source`, `partition`, positive integer `version`, and `rows`. Accounts, budgets, and coverage each use a complete `all` snapshot. Delivery uses `YYYY-MM-DD:channel`, replacing that whole business-date/channel partition. File names are descriptive; identity comes from the envelope and SHA-256 of the exact bytes.

Use ISO dates, inclusive effective/flight boundaries, America/Chicago business dates, USD only, integer impressions, and exact two-decimal dollar strings. IDs are nonempty strings; unknown fields are rejected. Channel is display, ctv, or audio. Amounts must be finite and nonnegative. No metric fills missing spend with zero.

The manifest is the source authority for the expected date/channel calendar; it must contain a continuous date range and every budget channel on every date. It must list exactly the campaign/account keys active in the effective budget plan. This lab has fixed account ownership and a single campaign ownership per campaign; historical owner changes are deferred.

| Source | Row key | Required row fields | Snapshot / correction policy |
| --- | --- | --- | --- |
| `accounts` | account_id | account_id, account_name, owner, agency, segment | Replace all account metadata; reject removals while referenced |
| `budgets` | campaign_id, channel, effective_from | campaign_id, account_id, channel, effective_from, effective_to, flight_start, flight_end, planned_daily_spend_usd | Replace all plans; effective ranges cannot overlap for a campaign/channel; campaign ownership is fixed |
| `coverage` | business_date, channel | business_date, channel, expected_keys | Replace entire calendar; expected_keys contains unique campaign_id/account_id pairs |
| `delivery` | campaign_id within date/channel partition | campaign_id, account_id, spend_usd, impressions | Replace partition; date/channel are envelope metadata; rows must equal manifest expected keys |

## Coverage and deletion

An expected active campaign with no activity has an explicit zero delivery row. If an expected delivery file is absent, acceptance of other valid inputs is allowed and that account-day stays incomplete. A received file omitting an expected key is invalid and fails the entire load attempt. An inactive campaign has no expected key. For an account with no active expected keys on a manifest date, planned and actual spend are defined as zero with `inactive` state.

Deleting a row from a corrected partition is valid only when the corrected budget and manifest retire that key too. Those files must arrive in the same load directory (or before the delivery correction where the resulting accepted state is already valid). The loader validates the combined final state atomically. Never replace an expected active row by omission.

## Versioning, lineage, and recovery

The same exact bytes at any path replay without adding raw records or changing accepted pointers. The same source/partition/version with different bytes is rejected. An unseen older version is rejected; the last accepted version remains current. Every accepted file retains exact bytes, parsed payload, checksum, path, business partition, version, receipt timestamp, row count, and accepting run.

A load attempt gets a persistent run record. A transaction validates and writes all proposed files and current pointers, or writes none. On failure the attempt is marked failed with an error after rollback. Retry valid bytes to recover. A database outage or forced process termination can leave a run in `running`; automatic abandoned-run reconciliation is later operational work.

The working mart reflects latest accepted restatements and is not an immutable historical as-of publication. Budget receipt-time modeling and published snapshots are later work. Missing files are data-coverage failures, not malformed load attempts. This distinction permits an explicit data investigation while preventing unsupported spend classification.

## References

The loader uses explicit transaction blocks described in the [Psycopg transaction documentation](https://www.psycopg.org/psycopg3/docs/basic/transactions.html). The local database uses the [official PostgreSQL Docker image](https://hub.docker.com/_/postgres).
