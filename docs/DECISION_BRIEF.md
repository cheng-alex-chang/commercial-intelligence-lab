# Decision brief — unexpected spend decline

All entities, values, rules, and workflows are fictional preparation exercises.

**User:** a Client Services account owner, supported by a commercial operations reviewer.

**Decision:** whether an active account needs a delivery investigation today. The output should help the owner decide what to inspect; it does not authorize client outreach or establish churn risk.

**Cadence:** daily after a fictional 09:00 America/Chicago cutoff for the previous business date. This slice uses historical fixtures and manual runs. Scheduling and cutoff enforcement are future work.

**Evidence:** two adjacent seven-day periods; observed advertiser spend; effective planned spend; account-level completeness; current owner; and source version references. Platform revenue is a different metric and is outside this first slice.

**Initial rule for the next milestone:** prior spend >= $50,000; decline >= 20% and >= $10,000; complete evidence; positive planned spend in both periods; current plan >= 90% of prior; and pacing decline >= 10 percentage points. Rank by observed dollars declined and cap at five accounts. These are provisional learning parameters.

**Routing:** complete unexpected declines go to the account owner. Missing expected delivery goes to the data reviewer. Ended flights with no current planned spend are planned changes. Observed zero spend remains zero; absent evidence remains unknown.

**Next action:** verify campaign constraints, budget changes, and delivery context. Include uncertainty rather than assuming a revenue loss or client-health diagnosis.

**Future evaluation:** delivery, review, time to review, usefulness, action, and dismissal reasons. Fixture accuracy verifies code behavior. A real user pilot would be needed to assess usefulness and impact.

## First technical handoff

Generate separate account, budget, coverage, and daily delivery files. Validate their relationships before changing accepted data. Preserve bytes and versions; transactionally replace complete partitions. Produce an account-day working view with spend NULL when expected delivery is missing. This working view supports debugging; a versioned, freshness-gated publication and investigation queue follow in M2.

## Learning checkpoint

Explain why Harbor's missing delivery must not look like Maple's observed zero, and why Beacon's scheduled flight ending must not look like Atlas's unexpected decline.
