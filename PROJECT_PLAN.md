# TTD Commercial Intelligence Lab — Revised Project Plan

**Reviewed:** October 7, 2026 · scope simplified after portfolio review

**Audience:** Software Engineer, Commercial Intelligence and Analytics; Senior Analyst, Commercial Intelligence & Analytics

**Status:** M0 complete; M1 implemented and verified at commercial scale October 7, 2026; public walkthrough and executive reporting implemented; M2 operational freshness work remains

Implementation notes: the first slice uses JSON source envelopes, latest accepted SQL views, and a dedicated PostgreSQL test database. It now generates complete-period comparisons, explainable account routes, and immutable report artifacts for the executive website and CSV. Operational cutoffs and persistent review tracking are pending. See [README.md](README.md) and [source contracts](docs/SOURCE_CONTRACTS.md) for the concrete implementation and current limits.

## 1. Outcome

Build a small commercial intelligence workflow that you can explain, validate, operate, and hand off:

> Which accounts should Client Services investigate today, what evidence supports the priority, who should review it, and what should they do next?

Begin with unexpected spend declines. Expand into portfolio revenue diagnosis and supported opportunity discovery after the investigation queue works.

Day-one preparation means being able to ask useful questions, inspect a model, identify unreliable evidence, propose a scoped solution, and communicate the next action. The project is practice for those habits. All accounts, prices, thresholds, and commercial definitions are fictional; none represents TTD's private systems.

## 2. Role alignment and source limits

The exact LinkedIn links supplied were unavailable through browsing. For the analyst, a search-accessible TTD careers description was available, although opening its URL subsequently returned 404. For engineering, a separate employer posting with the same title in Bellevue was accessible. Treat these as role-family evidence; exact equivalence to the supplied listings and current vacancy status are unverified.

The analyst description emphasizes defining commercial analyses, translating ambiguity into requirements, writing clear recommendations, partnering with technical teams, and evaluating whether signals support action. SQL, Python, metric quality, and validated AI-assisted work are part of the role. [TTD analyst description](https://careers.thetradedesk.com/jobs/5142999007/senior-analyst-commercial-intelligence-analytics).

The engineer description emphasizes the full lifecycle of intelligence systems, including architecture, implementation, deployment, monitoring, and iteration. It names Python, SQL, Snowflake, Tableau, Docker, Git/GitLab CI/CD, and LLM APIs. It also emphasizes workflow integration, testing, documentation, and signal adoption. [TTD software-engineer posting, Bellevue](https://www.linkedin.com/jobs/view/software-engineer-commercial-intelligence-and-analytics-at-the-trade-desk-4431541897).

The following deliverables are recommended exercises inferred from those responsibilities, rather than employer requirements for a preparation project.

| Capability to practice | Shared evidence | Analyst emphasis | Engineer emphasis |
| --- | --- | --- | --- |
| Commercial problem framing | Decision brief and acceptance examples | Stakeholder questions, alternatives, concise recommendation | Technical requirements and architecture tradeoffs |
| Trusted SQL/Python analysis | Reconciled account-day SQL view | Eligibility, comparison logic, explanatory narrative | Contracts, automated checks, incremental correctness |
| Proactive intelligence | Explainable daily investigation queue | Actionability and threshold calibration | Repeatable generation and reliable delivery |
| Workflow usefulness | Owner, review state, dismissal reason | Review burden and useful-signal assessment | Event instrumentation and deduplication |
| Operational readiness | Freshness evidence and recovery exercise | Communicate uncertainty and impact | CI, logs, rollback, deployment demonstration |
| AI judgment | One validated AI-assisted analysis task | Verify proposed SQL and narrative | Constrained interface and failure handling if extended |

## 3. Scope and architecture

**Core:** four source contracts, deterministic fixtures, Python batch ingestion, PostgreSQL business queries, scenario checks, and a daily website/CSV investigation report. Publish one brief explaining an account decision.

**Portfolio presentation:** a public GitHub repository, polished README, and static GitHub Pages walkthrough using a verified sample. Browser event controls illustrate source corrections and late arrival; they do not operate a backend queue.

**Analyst evidence:** decision requirements, comparison eligibility, threshold tradeoffs, and a short recommendation with uncertainty.

**Engineer evidence:** reproducible local setup, automated integration checks, atomic source acceptance, replay and correction handling, and a recovery explanation. These are part of the shared core, not a separate platform build.

```text
Four fictional source contracts
              |
Python: validate -> accept atomically
              |
PostgreSQL: source history + accepted pointers + SQL views
              |
Account-day CSV -> investigation report
              |
Owner, evidence, uncertainty, next check

Verified sample -> static GitHub Pages walkthrough
```

Use one PostgreSQL database and direct SQL views. There is no required medallion structure or separate staging/fact/mart hierarchy. Preserve exact source versions because they support replay and evidence. Review the grain of every join without creating redundant copies of the same data. The current implementation has three stored tables and source-specific views; see [architecture decisions](docs/ARCHITECTURE.md).

**Optional exercises after the core works:** one revenue bridge, one supported CRM opportunity, a Tableau view, a small Snowflake port, or a constrained AI-assisted analysis. Choose the exercise that closes an actual learning gap. dbt requires a model graph that benefits from it; an API requires a live consumer. A full warehouse migration, streaming stack, orchestration cluster, and deployed assistant are outside the core.

Spend a bounded learning session on Snowflake roles, warehouses, query history, and cost controls if that is unfamiliar. Port one validated query only if useful. These are learning choices, not claims about the team's internal architecture. A reused frontend is likewise optional; no existing prototype was supplied.

## 4. Decision requirements before coding

Write a one-page brief containing the user, decision, cadence, evidence, owner, and follow-up. Initial fictional users are a Client Services account owner and a commercial operations reviewer.

| Question to resolve | Initial project assumption |
| --- | --- |
| What decision changes? | Investigate an unexplained decline in active-account delivery |
| When is the queue needed? | Daily, after the source completeness cutoff |
| Who gets the signal? | The account owner as of the signal date |
| How much can they review? | A configurable daily capacity; default five accounts |
| What makes it actionable? | Valid evidence, a reason code, named owner, and a specific next check |
| What if evidence is incomplete? | Route to a data investigation and suppress commercial classification |
| What counts as useful? | The reviewer says the evidence informed a decision, with a recorded reason |

Prepare two handoffs: a business-facing brief and a technical contract explaining how the same requirement becomes data, logic, and checks.

## 5. Source contracts and fixture design

Use the default commercial profile: 1,000 fictional accounts, 5,000 campaigns, and 56 calendar dates, with normal-day simulated spend near $36.7 million. Use a fixed seed and a separate 10-account unit profile for fast tests. The financial reference and aggregate-versus-event distinction are documented in [SCALE_OVERVIEW.md](outputs/SCALE_OVERVIEW.md). Account/campaign counts and CPMs are synthetic design choices, not reported TTD facts. Separate inputs from expected outputs so scenario checks do not simply reproduce the rule implementation.

| Source | Grain / natural key | Required context |
| --- | --- | --- |
| Account metadata | Account ID | Owner, agency, segment; fixed for the core fixture |
| Campaign delivery | Campaign × business date × channel | Account, spend, impressions, source version |
| Campaign budget plan | Campaign × channel × effective-from date | Planned daily spend, flight dates, effective-to date |
| Coverage manifest | Source × business date × expected partition | Expected/received status, cutoff, file scope |
| Platform revenue — expansion | Account × business date | Recognized revenue, currency, accounting status/version |
| CRM opportunities — expansion | Opportunity × snapshot date | Account, stage, amount, close date, recorded interest |
| Service cases — later | Case × snapshot date | Account, opened/resolved dates, severity/category |

Use one currency, USD, and a documented business-date convention in the core. If the delivery provider uses a different timezone later, normalize it explicitly. Avoid mixing currency totals or partial days.

Each contract must define types, required fields, key, units, date semantics, version ordering, replacement scope, deletion policy, and completeness expectations. Budget versions must not overlap. For historical evaluation, use the budget and CRM information available at that time; preserve both effective dates and when information was received when those differ.

The coverage manifest also lists expected active campaign/channel keys. Delivery must include explicit zero rows for expected keys with no activity. A received file that omits an expected key fails completeness validation; file arrival alone does not establish entity coverage. A correction may remove an obsolete key only with a corresponding accepted update to expected coverage.

**File correction rule:** a delivery file is a complete snapshot for its declared business date and channel. An accepted newer version replaces that partition, including removal of omitted rows. Keep every raw version. Do not treat a corrected snapshot as an append or as an unspecified row-level patch.

Store checksum, file name, source version, partition, received time, row count, status, and error in the run ledger. Replay of the same checksum is a no-op. Validate the combined source state before accepting a partition. For the next milestone, each report records its generation time, period, source versions, and readiness. Publish only after required checks succeed; retain the last successful report with a visible stale flag if the next run fails. A simple report artifact is enough to start.

### Core scenario expectations

| Scenario | Expected classification | Evidence to demonstrate |
| --- | --- | --- |
| Atlas Retail: active flight, stable plan, genuine decline | Commercial investigation | Complete periods, material spend loss, lower pacing |
| Beacon Travel: flight ends as scheduled | Planned change | Scheduled budget explains the decline |
| Harbor Foods: delivery partition absent | Data investigation | Coverage is incomplete; spend stays unknown |
| Maple Goods: explicit complete zero-spend rows | Commercial investigation if eligibility passes | Zero is observed, rather than filled into an absent partition |
| Atlas file arrives twice | No change in totals or queue | Checksum replay is harmless |
| Atlas corrected file changes or removes rows | Latest accepted version governs | Totals and signals change once; history remains traceable |

Later add Cedar Auto: a discovery suggestion requires a fictional CRM record expressing channel interest, plus delivery evidence. Add a negative example with good performance and no stated interest. The latter should not automatically create an expansion recommendation.

## 6. Commercial models and metrics

Query typed accepted sources and build one account-day view. Aggregate measures before joining; preserve effective budget dates and expected coverage. In an optional revenue exercise, use a separate authoritative revenue source at its actual grain. Aggregate opportunity or case context before any join that could multiply spend.

Every metric entry contains a formula, unit, grain, eligible population, exclusions, date basis, owner, version, and freshness rule.

| Metric | Project definition / guardrail |
| --- | --- |
| Advertiser spend | Sum of accepted delivery spend for complete in-scope partitions |
| Planned spend | Sum of effective planned daily budgets across eligible campaigns/channels |
| Pacing | Actual spend / planned spend; undefined if planned spend is zero |
| Spend change | Current eligible-period spend minus prior eligible-period spend |
| Spend change percent | Change / prior spend; undefined for zero prior spend |
| Platform revenue | Sum from the separate fictional accounting source |
| Effective revenue yield | Revenue / spend for compatible complete periods; undefined for zero spend |
| Coverage | Received required partitions / expected required partitions |

Use two adjacent complete seven-day windows ending on the last eligible date. Their equal weekday composition reduces one simple comparison bias. Require the necessary delivery and budget coverage for each account, and show both periods. Mark new, inactive, or zero-baseline accounts separately. Keep incomplete accounts out of commercial ranking and disclose excluded account counts and known impact.

A portfolio bridge must distinguish continuing accounts, new accounts, inactive accounts, and exclusions. Reconcile the sum of those cohorts to the defined portfolio change; show a comparable-cohort result separately.

For accounts with positive spend in both periods, let `S` denote spend and `Y = revenue / spend`. Use the exact arithmetic bridge:

```text
Revenue change = (S1 - S0) × Y0 + S1 × (Y1 - Y0)
```

This ordering assigns the interaction term to yield. Label it a descriptive decomposition; mix, fees, and timing can affect yield. It is not a causal explanation or a claim about TTD's pricing. Keep zero-spend cases in a separate reconciliation category. Do not produce channel revenue unless a source or an explicit allocation model supports it.

## 7. Explainable signals and optional review pilot

Begin with a transparent fictional rule: prior seven-day spend at least $50,000, current spend at least 20% lower, absolute decline at least $10,000, complete data, positive planned spend in both periods, current planned spend at least 90% of prior, and current pacing at least 10 percentage points below prior. Accounts with larger planned reductions go to contextual review rather than this automatic unexpected-decline rule. Flight endings with no current plan are planned changes. These values are starting parameters for experimentation; they deliberately narrow the first rule to relatively stable plans.

Sort eligible signals by observed dollar decline, with reason codes visible. Cap the daily queue at the configured review capacity. Do not call the rank a churn probability or recovered-revenue estimate.

Each output includes account, owner, observation, both periods, actual/planned spend, completeness, rule version, evidence reference, uncertainty, and next check. For example: ask the owner to inspect active-campaign constraints after confirming the budget has not changed; client outreach remains a human decision.

If a review pilot is added, persist `new -> reviewed -> acted_on / dismissed`, with reviewer, timestamp, note, and dismissal reason. Maintain a stable account/rule/episode identifier so reruns do not create duplicate work. Record changed evidence and resolution; reopening requires a documented new episode policy.

In a review pilot, measure eligible signals, queue delivery, reviews, time to review, usefulness, actions, and dismissals. State each denominator. Synthetic fixtures measure expected classification and routing; simulated review events only verify instrumentation. Real adoption requires a user pilot. Spend recovery after review remains an observational result.

## 8. Milestones and acceptance gates

| Milestone | Deliverable | Completion evidence |
| --- | --- | --- |
| M0: decision and contracts — complete | Brief, four contracts, six scenario expectations | Can explain who acts, what evidence is needed, and when to suppress a signal |
| M1: trustworthy slice — complete | Generator, loader, account-day SQL view | Duplicate replay, correction/removal, failure recovery, missing, and zero scenarios behave correctly |
| M2: useful queue — report implemented; operational cutoffs pending | Repeatable executive website, comparison CSV, and account brief | Planned ending suppressed; actual decline explained; every item has owner, evidence, and next check |
| Portfolio presentation — implemented | Repository, README, static interactive site | Sample reconciles; published site works on desktop and mobile |
| Optional follow-up | Choose one revenue, CRM, BI, or warehouse learning exercise | New analysis reconciles and answers a defined question |

Run checks that protect business meaning: source-to-output reconciliation to documented currency precision, unique keys, valid relationships, ratio aggregation, coverage gating, budget effective dates, replay/correction behavior, and scenario outputs. A source check failure must block new publication. CI runs a small PostgreSQL integration fixture and reproduces the commercial sample before deploying the static walkthrough. Extend it to report publication when M2 exists.

Demonstrate a clean local run, meaningful failure and retry, readable run status, and a short explanation of stale evidence. Record actual timings for the larger commercial profile. Add a repeatable report command in M2; scheduling can follow when cadence needs it. A local container and static website do not demonstrate operating a production cloud intelligence service.

Keep API endpoints, persistent review storage, and multi-user access enforcement as optional follow-ups. A live consumer would justify the first; a real review pilot would justify the second. The static walkthrough is a portfolio explanation rather than a live operating tool.

## 9. Time plan

Keep the original cadence of four 30–60 minute sessions weekly as an assumption until your availability is known. The original four-week schedule provides 8–16 hours; use it only for M0–M2 at minimal scope, assuming existing Python/SQL familiarity and a working local database.

| Week | Small-core sessions |
| --- | --- |
| 1 | Decision brief; source contracts; scenario expectations; fixture generator |
| 2 | Loader and ledger; replay; partition replacement; coverage handling |
| 3 | Account-day SQL; reconciliation; period eligibility; first signal |
| 4 | Remaining scenarios; daily queue; account brief; walkthrough and fixes |

If a milestone takes longer, extend the calendar or reduce source breadth. Keep the correctness gates. If setup consumes week one, deliver a reviewed SQL/fixture exercise first and shift ingestion into the next week.

Finish M2 and a five-minute walkthrough before expanding. Reserve a separate bounded session for any optional tool or domain exercise. The original estimate of 8–16 focused hours for the minimal core assumes familiar Python/SQL and working local tooling; it is a planning assumption, not a delivery promise. Retire an optional exercise if it does not improve the business explanation or expose a useful failure case.

## 10. AI practice and optional assistant

During the core, use an AI tool for one bounded task, such as proposing reconciliation SQL or drafting a metric definition. Save the proposal, independently verified result, errors found, and final correction. This practices validation without delaying the workflow.

An optional assistant follows validated queries and stable interfaces. Constrain it to account summaries, revenue changes, priority lists, and metric definitions. Require structured tool results with scope, period, freshness, and evidence. The interface should clarify ambiguous revenue terms and disclose incomplete data.

Evaluate at least ten fixed questions covering correct arithmetic, ambiguous periods/metrics, missing data, unsupported causal claims, tool failures, and unauthorized scope. Validate numerical assertions against trusted expected answers. Enforce scope in the service, rather than relying on the assistant's instructions. Keep unrestricted raw SQL execution outside this extension.

## 11. Learning evidence and day-one readiness

Practice a five-minute walkthrough: business question, definitions, source grain, one misleading comparison, correct analysis, action, and operating failure. Then explain the same case once to an account owner and once to an engineer.

Complete a short domain glossary covering advertiser, agency, campaign flight, budget pacing, DSP, auction/bid/win, CTV, attribution window, and spend versus platform revenue. Label simplified fictional assumptions. Explain why conversion data can arrive late and why a lower-spend week need not mean lost-client risk.

Bring these questions into onboarding:

1. Who uses these signals, and what decisions do they make each day?
2. Which commercial and accounting definitions are authoritative, and who owns them?
3. How are advertiser, agency, campaign, and account identities related?
4. What are the expected freshness, correction, and period-close policies?
5. Which changes are planned, seasonal, or caused by incomplete coverage?
6. Where should intelligence reach users, and how is review/action measured?
7. What are the team's deployment, monitoring, access, and incident practices?
8. Which existing assets should be reused before building anything new?

The preparation package is complete when the chosen scope passes its gates and you can defend its assumptions and limitations. M0 and the first M1 slice now pass their checks. The executive briefing now compares complete seven-day periods, generates ranked priorities, exposes exclusions and evidence, and preserves successful snapshots. Finish M2 with operational cutoff/freshness handling and a short decision memo before expanding tools.
