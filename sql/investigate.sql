-- Run these against the local lab with your SQL client.
-- Observe NULL versus zero on the final business date.
SELECT account_name, business_date, spend_usd, planned_spend_usd,
       data_state, missing_partitions, evidence
FROM lab.account_day_working
WHERE business_date = DATE '2026-08-31'
ORDER BY account_name;

-- SUM ignores NULL, so gate period totals on completeness explicitly.
SELECT account_id,
       CASE WHEN COUNT(*) FILTER (WHERE data_state = 'missing_delivery') > 0
            THEN NULL ELSE SUM(spend_usd) END AS period_spend_usd,
       SUM(planned_spend_usd) AS period_planned_spend_usd,
       COUNT(*) FILTER (WHERE data_state = 'missing_delivery') AS missing_days
FROM lab.account_day_working
WHERE business_date BETWEEN DATE '2026-08-25' AND DATE '2026-08-31'
GROUP BY account_id ORDER BY account_id;

SELECT run_id, status, accepted_files, replayed_files, error
FROM lab.ingestion_runs ORDER BY started_at DESC;
