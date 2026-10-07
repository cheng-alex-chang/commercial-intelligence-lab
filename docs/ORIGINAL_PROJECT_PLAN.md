# Commercial Intelligence Platform — Project Plan

## Purpose

Build an end-to-end commercial analytics system, starting with the data pipeline and progressing through warehouse modeling, business signals, a backend, and a dashboard. Add governed AI analytics after the foundation works.

This is a preparation project for a Senior Commercial Intelligence & Analytics Analyst role at The Trade Desk. The emphasis is on understanding business questions and deciding what should be built, alongside implementing reliable analytics.

**Central business question:**

> Which accounts should Client Service investigate today, what evidence supports that recommendation, and what action should they consider?

All data, entities, commercial definitions, and pricing assumptions are fictional. The project does not represent TTD's internal systems or actual metrics.

## Current State

The existing Commercial Intelligence Lab is a frontend prototype. It generates a fictional dataset and calculates metrics in JavaScript. It provides a reference for the business questions and interface, but does not yet have ingestion, warehouse models, a backend, or a real semantic layer.

The next stage is to build the underlying system from the ground up and connect the dashboard to it.

## Initial Business Outputs

1. **Account prioritization:** identify unexpected spend declines, unresolved service issues, and expansion opportunities.
2. **Revenue diagnosis:** explain which accounts contributed to a change and whether spend or revenue yield explains it.
3. **Governed business answers:** expose consistent metrics through dashboards and, eventually, an AI agent.

## Proposed Architecture

Start locally with **Python, PostgreSQL, dbt, and FastAPI**. Move the warehouse to Snowflake later to practice its operational concepts after the business logic works.

| Layer | What we build | Why it matters |
| --- | --- | --- |
| Source data | Separate delivery, CRM, budget, revenue, and service datasets | Commercial questions require context across systems |
| Ingestion | Python batch loaders with run tracking and replay support | Corrected files and failed runs must be recoverable |
| Raw storage | Source records with ingestion metadata | Preserve evidence for reconciliation and debugging |
| Modeling | dbt staging, dimensions, facts, and marts | Establish consistent grain, joins, and business definitions |
| Analytics | SQL metrics, revenue comparisons, and explainable signals | Turn reliable data into useful decisions |
| Serving | FastAPI endpoints backed by warehouse queries | Give the dashboard and future agent one governed interface |
| Consumption | Dashboard, account investigation, and approved question tools | Put evidence into stakeholder workflows |

## Phase 1 — Source Contracts and Ingestion

### Source datasets

| Dataset | Grain | Example fields |
| --- | --- | --- |
| Campaign delivery | Campaign × date × channel | Spend, impressions, bids, wins, conversions |
| Campaign budgets | Campaign × effective date | Planned budget, flight dates, status |
| CRM accounts | Account | Agency, owner, segment |
| CRM opportunities | Opportunity | Account, stage, amount, expected close date |
| Service cases | Case | Account, category, opened date, resolved date |
| Platform revenue | Account × date | Recognized revenue amount |

Keep advertiser spend and platform revenue separate. Their relationship needs an explicit definition; they are not interchangeable measures.

### Build

- Create a deterministic generator that produces daily source files rather than one dashboard-ready JSON file.
- Define the grain, primary key, required fields, types, and correction policy for each source.
- Load source records into raw tables while preserving source evidence.
- Record filename, checksum, ingestion time, business date, and run status.
- Support replay and corrections without double-counting.
- Represent expected delivery coverage so absent records can be distinguished from genuine zero activity.

### Exercise realistic failures

- A file arrives late.
- A corrected delivery file replaces an earlier version.
- The same file is loaded twice.
- An account has zero spend.
- An account's delivery records are missing.

### Acceptance checks

- Rerunning a file does not double-count it.
- A correction updates the intended records while preserving its source history.
- A failed run can be recovered without producing partial analytical results.
- Missing data remains distinguishable from zero activity.

## Phase 2 — Trustworthy Commercial Models

### Build

- Staging models that standardize types, identifiers, and dates.
- Account and campaign dimensions.
- Delivery, revenue, opportunity, and service facts.
- An account-day mart combining the information needed for analysis.
- Metric definitions documenting formula, grain, exclusions, date interpretation, and freshness requirements.

### Key modeling exercise

Join sources without multiplying measures. Joining daily spend directly to multiple opportunities and service cases can inflate totals. Aggregate each source to the required grain before combining it with other sources.

### Acceptance checks

- Source totals reconcile with warehouse totals.
- Joins preserve additive measures.
- Keys and relationships are validated.
- Incomplete periods are flagged.
- Ratio metrics are calculated from their appropriate numerators and denominators.

## Phase 3 — Business Analysis and Signals

Use this workflow for every analysis:

**Business question → metric definition → dimensions → data → analysis → signal → action**

### Initial scenarios

| Scenario | Analysis | Suggested action |
| --- | --- | --- |
| Atlas Retail's spend falls | Compare equal periods, scheduled budget, pacing, and completeness | Investigate an unexpected delivery decline |
| Beacon Travel's spend falls | Check campaign flight dates and planned budget reduction | Recognize the planned ending |
| Cedar Auto performs well | Review outcomes, channel mix, CRM interest, and delivery capacity | Explore a CTV discovery conversation |

### Build

- Equal-length period comparisons with explicit account eligibility.
- Account contributions to revenue change.
- Spend and revenue-yield decomposition where the underlying definitions support it.
- Transparent rules for investigation priorities.
- Supporting evidence and suggested next steps for each signal.

Use the term **investigation priority** for initial rule-based signals. Do not present them as validated churn probabilities or causal revenue forecasts.

### Acceptance checks

- Every recommendation includes an observation, relevant context, uncertainty, and a reasonable next step.
- Planned campaign endings do not trigger unexpected-decline signals.
- Missing records trigger a data investigation rather than an unsupported client-health claim.
- Account contributions reconcile to the comparable portfolio change.

## Phase 4 — Backend and Dashboard

### Build

Replace frontend calculations with warehouse-backed endpoints for:

- Portfolio metrics.
- Account priorities and supporting evidence.
- Account history.
- Revenue movement by account and channel.
- Metric definitions and data freshness.

Move investigation notes into persistent storage. Track whether a signal was reviewed, useful, dismissed, or acted on.

### Business evaluation

> Is this helping Client Service decide where to spend its time?

Capture reviewer feedback and reasons for dismissal. A later spend recovery can be recorded as an observational outcome; it does not by itself establish that an intervention caused the recovery.

### Acceptance checks

- Dashboard values agree with warehouse queries under the same scope and period.
- Responses expose their period, scope, definitions, and freshness.
- Investigation notes survive browser reloads and are stored in the backend.
- A reviewer can understand why an account was prioritized.

## Phase 5 — Governed AI Analytics

Add this after the underlying metrics and business workflows work.

### Approved tools

- `get_account_summary`
- `get_revenue_change`
- `list_account_priorities`
- `get_metric_definition`

Each tool returns structured results with scope, period, definition, freshness, and supporting evidence.

The agent selects constrained tools, explains returned results, and asks for clarification when terms such as "revenue" or "client health" are ambiguous. It should not freely execute SQL against raw tables.

### Evaluation

- Known questions with verified answers.
- Missing-data scenarios.
- Ambiguous metric names.
- Incorrect assumptions embedded in questions.
- Unsupported requests.
- Account access and scope restrictions before any multi-user deployment.

### Acceptance checks

- Numerical claims match approved tool results.
- Ambiguous questions receive clarification.
- Incomplete data is disclosed.
- Unsupported requests do not produce invented answers.
- Results remain within the caller's permitted scope.

## Four-Week MVP Schedule

Target approximately **30–60 minutes per session, four days per week**. Keep each phase small enough to produce one reviewable result. Treat the AI agent and Snowflake migration as extensions after the core pipeline works.

| Week | Deliverable |
| --- | --- |
| 1 | Source contracts, daily fixtures, ingestion, and replay |
| 2 | Warehouse models, metric definitions, and reconciliation |
| 3 | Revenue analysis and three explainable account scenarios |
| 4 | API, dashboard integration, and stakeholder walkthrough |

If setup or implementation exceeds the available sessions, narrow the MVP to delivery, budgets, and account metadata first. Add opportunities and service cases after that vertical slice works.

## First Build Milestone

**Ingest daily campaign delivery and budget files, then produce an account-day table that correctly handles duplicate files, corrections, zero spend, and missing records.**

The business outcome is a trustworthy foundation for answering whether a spend decline deserves commercial attention.

