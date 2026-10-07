# An executive briefing from the same data

The website answers three questions: what changed across the comparable portfolio, which accounts warrant an owner review, and which gaps or planned changes limit the interpretation. It uses the same Python report output as the downloadable comparison CSV. The browser formats results; it does not independently classify accounts or calculate portfolio aggregates.

## What the sample says

The reporting windows are August 18–24 and August 25–31, 2026. Both portfolio totals use the same 999 complete accounts. One incomplete account, Harbor, is excluded from both windows. Comparison coverage is an account count, not a share of spend.

| Complete-account group | Accounts | Observed spend change |
| --- | ---: | ---: |
| Unexpected-decline rule: Maple and Atlas | 2 | -$4,550,000.00 |
| Planned ending: Beacon | 1 | -$2,800,000.00 |
| Other complete accounts | 996 | -$21,232.89 |
| Total comparable portfolio | 999 | -$7,371,232.89 |

Prior spend is $254,176,513.25; current spend is $246,805,280.36. Harbor's known prior amount is $2.8M and known current partial amount is $2.4M. Neither appears in the comparable totals; Harbor's incomplete period remains unknown. The bridge groups reconcile exactly, while grouping and budget context remain descriptive rather than causal conclusions.

## Eligibility and actions

The initial rule requires prior spend ≥ $50,000, a decline ≥ 20% and ≥ $10,000, complete evidence, positive plans, a current plan ≥ 90% of prior, and a pacing decline ≥ 10 percentage points. Integer cents and exact cross-products preserve money and threshold comparisons, including repeating pacing ratios. Rank eligible accounts by observed dollar decline, breaking ties by account ID. Capacity defaults to five and deferred counts remain visible.

Missing delivery produces a data investigation. A current zero plan after a positive prior plan produces a planned change. A material plan reduction needs contextual review; a zero prior baseline cannot support a decline percentage. Explicit observed zero remains eligible for review when the other conditions hold.

Each surfaced account has an owner, prior/current spend and plan, completeness, a next check, and expandable source references. The account owner determines the cause and any client action. The report does not measure revenue loss or validated churn risk.

## Publication and use

`ttd-lab report --end-date 2026-08-31` reads the accepted account-day SQL view, validates the two-window shape, builds a shared comparison, and publishes into `outputs/reports/`. Set `--output site/reports` to view the result in the static website. The command is manual; it is not scheduled.

Snapshot directories contain JSON and account-comparison CSV under a digest covering all report data, including the full account comparisons and evidence. Files are prepared in a temporary directory, then renamed into place. Only after completion does `latest.json` advance atomically. The website resolves the pointer once, so the page and download refer to the same snapshot. Previous snapshots stay available; existing snapshots cannot be rewritten with different contents. This is report artifact versioning, not a historical as-of database model.

The public sample is reproducible from a fresh baseline export using `scripts/build_report.py`, after `scripts/build_demo.py` has reconciled the full baseline. CI verifies both samples before Pages deployment. The historical end date is prominent; the briefing makes no claim of current operational freshness.

## Verification and remaining work

Checks cover independent scenario routing/totals, prior and current missingness, observed zero, plan changes, zero baselines, ranking/capacity, duplicate days, incomplete window shape, currency precision, exact cohort reconciliation, correction and late-file effects, CSV amounts, immutable replay, and failed publication retaining the previous pointer.

Desktop/mobile presentation and expandable evidence are reviewed in the browser. The print button invokes the browser's print dialog with a dedicated print stylesheet; CSV remains optional. The public website has no authenticated review workflow, database connection, operational scheduler, or automatic freshness cutoff. Those are separate learning increments if needed.
