CREATE SCHEMA IF NOT EXISTS lab;

CREATE TABLE IF NOT EXISTS lab.ingestion_runs (
    run_id UUID PRIMARY KEY,
    input_path TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    accepted_files INTEGER NOT NULL DEFAULT 0,
    replayed_files INTEGER NOT NULL DEFAULT 0,
    error TEXT
);

CREATE TABLE IF NOT EXISTS lab.raw_files (
    file_id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL CHECK (source IN ('accounts', 'budgets', 'coverage', 'delivery')),
    partition_key TEXT NOT NULL,
    source_version INTEGER NOT NULL CHECK (source_version > 0),
    checksum TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    row_count INTEGER NOT NULL CHECK (row_count >= 0),
    raw_bytes BYTEA NOT NULL,
    payload JSONB NOT NULL,
    accepted_run_id UUID NOT NULL REFERENCES lab.ingestion_runs(run_id),
    UNIQUE (source, partition_key, source_version)
);

CREATE TABLE IF NOT EXISTS lab.current_files (
    source TEXT NOT NULL,
    partition_key TEXT NOT NULL,
    file_id BIGINT UNIQUE NOT NULL REFERENCES lab.raw_files(file_id),
    PRIMARY KEY (source, partition_key)
);

CREATE OR REPLACE VIEW lab.accepted_files AS
SELECT r.* FROM lab.current_files c JOIN lab.raw_files r USING (file_id);

CREATE OR REPLACE VIEW lab.accounts AS
SELECT a.*, f.file_id AS source_file_id
FROM lab.accepted_files f CROSS JOIN LATERAL jsonb_to_recordset(f.payload->'rows')
    AS a(account_id TEXT, account_name TEXT, owner TEXT, agency TEXT, segment TEXT)
WHERE f.source = 'accounts';

CREATE OR REPLACE VIEW lab.budgets AS
SELECT b.*, f.file_id AS source_file_id
FROM lab.accepted_files f CROSS JOIN LATERAL jsonb_to_recordset(f.payload->'rows')
    AS b(campaign_id TEXT, account_id TEXT, channel TEXT, effective_from DATE,
         effective_to DATE, flight_start DATE, flight_end DATE,
         planned_daily_spend_usd NUMERIC(18,2))
WHERE f.source = 'budgets';

CREATE OR REPLACE VIEW lab.coverage AS
SELECT c.*, c.business_date::TEXT || ':' || c.channel AS partition_key,
       f.file_id AS source_file_id
FROM lab.accepted_files f CROSS JOIN LATERAL jsonb_to_recordset(f.payload->'rows')
    AS c(business_date DATE, channel TEXT, expected_keys JSONB)
WHERE f.source = 'coverage';

CREATE OR REPLACE VIEW lab.expected_delivery AS
SELECT c.business_date, c.channel, c.partition_key, k.campaign_id, k.account_id,
       c.source_file_id AS coverage_file_id
FROM lab.coverage c CROSS JOIN LATERAL jsonb_to_recordset(c.expected_keys)
    AS k(campaign_id TEXT, account_id TEXT);

CREATE OR REPLACE VIEW lab.delivery AS
SELECT split_part(f.partition_key, ':', 1)::DATE AS business_date,
       split_part(f.partition_key, ':', 2) AS channel, d.*, f.file_id AS source_file_id
FROM lab.accepted_files f CROSS JOIN LATERAL jsonb_to_recordset(f.payload->'rows')
    AS d(campaign_id TEXT, account_id TEXT, spend_usd NUMERIC(18,2), impressions BIGINT)
WHERE f.source = 'delivery';

-- This is a working view of accepted source state, not a published snapshot.
CREATE OR REPLACE VIEW lab.account_day_working AS
WITH required AS (
    SELECT e.account_id, e.business_date, COUNT(*) AS expected_keys,
           COUNT(DISTINCT e.partition_key) FILTER (WHERE f.file_id IS NULL) AS missing_partitions,
           SUM(b.planned_daily_spend_usd) AS planned_spend_usd,
           jsonb_agg(jsonb_build_object('partition', e.partition_key,
               'coverage_file_id', e.coverage_file_id, 'budget_file_id', b.source_file_id,
               'delivery_file_id', f.file_id, 'delivery_version', f.source_version)
               ORDER BY e.channel, e.campaign_id) AS evidence
    FROM lab.expected_delivery e
    JOIN lab.budgets b ON b.campaign_id = e.campaign_id AND b.account_id = e.account_id
      AND b.channel = e.channel AND e.business_date BETWEEN b.effective_from AND b.effective_to
      AND e.business_date BETWEEN b.flight_start AND b.flight_end
    LEFT JOIN lab.accepted_files f ON f.source = 'delivery' AND f.partition_key = e.partition_key
    GROUP BY e.account_id, e.business_date
), actual AS (
    SELECT account_id, business_date, SUM(spend_usd) AS spend_usd,
           SUM(impressions) AS impressions
    FROM lab.delivery GROUP BY account_id, business_date
), dates AS (
    SELECT DISTINCT business_date FROM lab.coverage
)
SELECT a.account_id, a.account_name, a.owner, d.business_date,
       CASE WHEN r.missing_partitions > 0 THEN NULL
            ELSE COALESCE(t.spend_usd, 0) END AS spend_usd,
       COALESCE(r.planned_spend_usd, 0) AS planned_spend_usd,
       CASE WHEN r.missing_partitions > 0 THEN NULL
            ELSE COALESCE(t.impressions, 0) END AS impressions,
       COALESCE(r.expected_keys, 0) AS expected_keys,
       COALESCE(r.missing_partitions, 0) AS missing_partitions,
       CASE WHEN r.missing_partitions > 0 THEN 'missing_delivery'
            WHEN r.expected_keys IS NULL THEN 'inactive' ELSE 'complete' END AS data_state,
       COALESCE(r.evidence, '[]'::JSONB) AS evidence,
       a.source_file_id AS account_file_id
FROM lab.accounts a CROSS JOIN dates d
LEFT JOIN required r ON r.account_id = a.account_id AND r.business_date = d.business_date
LEFT JOIN actual t ON t.account_id = a.account_id AND t.business_date = d.business_date;
