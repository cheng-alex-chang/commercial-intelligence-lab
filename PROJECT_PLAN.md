# TTD Commercial Intelligence Lab — Revised Project Plan

**Reviewed:** October 6, 2026

**Audience:** Software Engineer, Commercial Intelligence and Analytics; Senior Analyst, Commercial Intelligence & Analytics

**Status:** M0 complete; M1 implemented and verified October 6, 2026; M2 next

Implementation notes: the first slice uses JSON source envelopes, latest accepted SQL views, and a dedicated PostgreSQL test database. It does not yet publish immutable snapshots or generate signals. See [README.md](README.md) and [source contracts](docs/SOURCE_CONTRACTS.md) for the concrete implementation and current limits.

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
| Trusted SQL/Python analysis | Reconciled account-day mart | Eligibility, comparison logic, explanatory narrative | Contracts, automated checks, incremental correctness |
| Proactive intelligence | Explainable daily investigation queue | Actionability and threshold calibration | Repeatable generation and reliable delivery |
| Workflow usefulness | Owner, review state, dismissal reason | Review burden and useful-signal assessment | Event instrumentation and deduplication |
| Operational readiness | Freshness evidence and recovery exercise | Communicate uncertainty and impact | CI, logs, rollback, deployment demonstration |
| AI judgment | One validated AI-assisted analysis task | Verify proposed SQL and narrative | Constrained interface and failure handling if extended |

## 3. Scope and architecture

**Core:** four source contracts, deterministic fixtures, Python batch ingestion, PostgreSQL SQL models, scenario checks, and a generated daily CSV/Markdown queue. Publish one brief explaining an account decision.

**Shared expansion:** platform revenue, CRM snapshots, a reconciled revenue bridge, a repeatable run, and an instrumented review workflow.

**Analyst branch:** stakeholder requirements, threshold analysis, one BI view, and an executive decision memo.

**Engineer branch:** dbt, containerized setup, CI, API, a deployment/release demonstration, monitoring, and a recovery runbook.

**Later extensions:** service cases, renewal/commitment examples, product telemetry, an LLM assistant, and fuller frontend integration. Renewal analysis requires a defined renewal event or commitment source; a scheduled campaign ending is insufficient.

```text
Fictional daily files + completeness manifest
                 |
          Python batch loader
                 |
     Immutable raw versions + run ledger
                 |
     Staging -> facts/dimensions -> validated marts
                 |
     Versioned published snapshot + signal rules
                 |
     Daily queue -> owner review -> feedback events
                 |
       BI view / optional API / optional assistant
```

PostgreSQL is the default local warehouse. Keep core transformations as reviewed SQL if learning dbt would delay the first useful output. Adopt dbt for the expanded model graph rather than maintaining two independent sets of business logic.

Spend an early learning session on Snowflake roles, warehouses, query history, and cost controls. After local reconciliation succeeds, port only one mart and verify matching results. A full warehouse migration is optional. Use Tableau for the BI exercise when accessible; a local chart or exported view keeps progress possible otherwise. These are recommended learning choices, not claims about the team's internal architecture.

Reuse the existing frontend only after inspecting its code and confirming that it can consume the governed outputs. The original plan mentions it, but no prototype was supplied here.

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

Start with 10–20 accounts and 56 business dates, enough for equal-length comparisons and several campaign endings. Use a fixed seed. Separate inputs from expected outputs so scenario checks do not simply reproduce the rule implementation.

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

Store checksum, file name, source version, partition, received time, row count, status, and error in the run ledger. Replay of the same checksum is a no-op. Stage and validate before accepting a partition. A mart publication has its own batch ID and readiness state; publish only after every required input and check for that snapshot succeeds. Readers retain the last successful snapshot with a visible stale flag if the next run fails.

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

Build account and campaign dimensions, delivery facts, effective budget plans, and an account-day mart. Aggregate each source to account-day before joining. Add revenue independently at its actual grain. Keep opportunities and cases as separate facts, aggregating only the context needed for a particular output.

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

## 7. Explainable signal and review workflow

Begin with a transparent fictional rule: prior seven-day spend at least $1,000, current spend at least 20% lower, absolute decline at least $500, complete data, positive planned spend in both periods, current planned spend at least 90% of prior, and current pacing at least 10 percentage points below prior. Accounts with larger planned reductions go to contextual review rather than this automatic unexpected-decline rule. Flight endings with no current plan are planned changes. These values are starting parameters for experimentation; they deliberately narrow the first rule to relatively stable plans.

Sort eligible signals by observed dollar decline, with reason codes visible. Cap the daily queue at the configured review capacity. Do not call the rank a churn probability or recovered-revenue estimate.

Each output includes account, owner, observation, both periods, actual/planned spend, completeness, rule version, evidence reference, uncertainty, and next check. For example: ask the owner to inspect active-campaign constraints after confirming the budget has not changed; client outreach remains a human decision.

Persist `new -> reviewed -> acted_on / dismissed`, with reviewer, timestamp, note, and dismissal reason. Maintain a stable account/rule/episode identifier so reruns do not create duplicate work. Record changed evidence and resolution; reopening requires a documented new episode policy.

Measure eligible signals, queue delivery, reviews, time to review, usefulness, actions, and dismissals. State each denominator. Synthetic fixtures measure expected classification and routing; simulated review events only verify instrumentation. Real adoption requires a user pilot. Spend recovery after review remains an observational result.

## 8. Milestones and acceptance gates

| Milestone | Deliverable | Completion evidence |
| --- | --- | --- |
| M0: decision and contracts | Brief, four contracts, six scenario expectations | Can explain who acts, what evidence is needed, and when to suppress a signal |
| M1: trustworthy slice | Generator, loader, SQL mart | Duplicate replay, correction/removal, failure recovery, missing, and zero scenarios behave correctly |
| M2: useful queue | Repeatable daily CSV/Markdown output and account brief | Planned ending suppressed; actual decline explained; every item has owner, evidence, and next check |
| M3: revenue and context | Revenue bridge, CRM snapshots, persistent review events | Source totals reconcile; cohorts and bridge reconcile; no join fanout or future-context leakage |
| M4A: analyst branch | BI view, threshold study, two-page decision memo | Same governed metrics; burden/coverage tradeoffs clear; limitations and next decision explicit |
| M4E: engineer branch | dbt models, container setup, CI, API/release demo, runbook | Clean setup works; automated checks gate publication; failed release/refresh recovery demonstrated |

Run checks that protect business meaning: source-to-mart reconciliation to documented currency precision, unique keys, valid relationships, ratio aggregation, coverage gating, budget effective dates, replay/correction behavior, and scenario outputs. A source check failure must block new publication. CI for the engineering branch must run a small integration fixture through ingestion, modeling, and publication.

For the engineering branch, demonstrate execution from a clean local environment, a scheduled or repeatable batch trigger, structured logs, run status, and freshness warning. Document how to restore the last successful mart after a failed refresh or code change. Benchmark a larger generated dataset and record actual timings/query plans; set a performance target based on that baseline. A local container release is a valid preparation exercise, but does not demonstrate operating a production cloud service.

The optional API initially needs portfolio summary, account evidence, priorities, metric definitions, and review events. Return snapshot ID, period, scope, exclusions, and freshness. Any reused dashboard must match SQL outputs under identical filters. Add scope enforcement and authorization tests before a multi-user extension.

## 9. Time plan

Keep the original cadence of four 30–60 minute sessions weekly as an assumption until your availability is known. The original four-week schedule provides 8–16 hours; use it only for M0–M2 at minimal scope, assuming existing Python/SQL familiarity and a working local database.

| Week | Small-core sessions |
| --- | --- |
| 1 | Decision brief; source contracts; scenario expectations; fixture generator |
| 2 | Loader and ledger; replay; partition replacement; coverage handling |
| 3 | Account-day SQL; reconciliation; period eligibility; first signal |
| 4 | Remaining scenarios; daily queue; account brief; walkthrough and fixes |

If a milestone takes longer, extend the calendar or reduce source breadth. Keep the correctness gates. If setup consumes week one, deliver a reviewed SQL/fixture exercise first and shift ingestion into the next week.

Planning estimates for the whole revised scope, including the small core:

| Scope | Estimated total focused effort | At 2–4 hours/week |
| --- | --- | --- |
| Minimal core M0–M2 | 8–16 hours if tools are familiar | About 4 weeks; extend if needed |
| Shared foundation plus analyst branch | 24–36 hours | Roughly 6–18 weeks |
| Shared foundation plus engineer branch | 32–48 hours | Roughly 8–24 weeks |
| Both branches | 40–60 hours | Roughly 10–30 weeks |

These are planning estimates, not delivery promises; tool learning and troubleshooting add time. If day one is close, finish one reliable decline investigation, a short decision memo, and the onboarding questions below before expanding infrastructure.

## 10. AI practice and optional assistant

During the core, use an AI tool for one bounded task, such as proposing reconciliation SQL or drafting a metric definition. Save the proposal, independently verified result, errors found, and final correction. This practices validation without delaying the workflow.

An optional assistant follows validated marts and stable interfaces. Constrain it to account summaries, revenue changes, priority lists, and metric definitions. Require structured tool results with scope, period, freshness, and evidence. The interface should clarify ambiguous revenue terms and disclose incomplete data.

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

The preparation package is complete when the chosen scope passes its gates and you can defend its assumptions and limitations. M0 and the first M1 slice now pass their checks. The next action is M2: define complete seven-day comparisons, generate the evidence-backed investigation queue, and gate published outputs on validation and freshness.
