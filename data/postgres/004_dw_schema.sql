-- claimsdb, schema dw: the small premium and claims warehouse. Owner: @corvane/data-platform.
-- Billing lineage: PRMBILL -> CORV.PRM.BILLING.DAILY (BILLREC, 64 bytes) -> SFTP /landing/billing/
--   -> Airflow DAG premium_billing_load -> warehouse-loader load_billing_file -> dw.premium_billing_stage
--   -> dw.fn_merge_billing() -> dw.premium_billing -> dw.v_premium_by_line and dw.mv_premium_by_line_month.
-- Claims lineage: claims-service -> claims.closed.v1 -> warehouse-loader closed_claims -> dw.claim_closed_fact.

CREATE SCHEMA IF NOT EXISTS dw;

-- One row per billing file. warehouse-loader inserts (file_name, record_count, started_at) and sets
-- merged_count and finished_at after dw.fn_merge_billing().
CREATE TABLE dw.billing_load (
    load_id          bigserial PRIMARY KEY,
    file_name        varchar(120) NOT NULL UNIQUE,
    record_count     integer NOT NULL,
    merged_count     integer,
    status           varchar(10) NOT NULL DEFAULT 'STAGED'
                       CHECK (status IN ('STAGED','MERGED','REJECTED')),
    rejected_reason  varchar(200),
    started_at       timestamptz NOT NULL DEFAULT now(),
    finished_at      timestamptz
);

-- One row per BILLREC record, decoded by warehouse-loader (zoned decimal, sign overpunched, 2 implied dp).
CREATE TABLE dw.premium_billing_stage (
    stage_id     bigserial PRIMARY KEY,
    load_id      bigint NOT NULL REFERENCES dw.billing_load(load_id) ON DELETE CASCADE,
    policy_no    varchar(12) NOT NULL,
    line_code    char(3) NOT NULL,
    bill_date    date NOT NULL,
    premium_amt  numeric(11,2) NOT NULL,
    ipt_amt      numeric(9,2) NOT NULL,
    currency     char(3) NOT NULL,
    region       char(2) NOT NULL
);
CREATE INDEX ix_premium_billing_stage_load ON dw.premium_billing_stage(load_id);

CREATE TABLE dw.premium_billing (
    policy_no    varchar(12) NOT NULL,
    line_code    char(3) NOT NULL,
    bill_date    date NOT NULL,
    premium_amt  numeric(11,2) NOT NULL,
    ipt_amt      numeric(9,2) NOT NULL,
    currency     char(3) NOT NULL,
    region       char(2) NOT NULL,
    load_id      bigint NOT NULL REFERENCES dw.billing_load(load_id),
    loaded_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (policy_no, line_code, bill_date)
);
CREATE INDEX ix_premium_billing_line_date ON dw.premium_billing(line_code, bill_date);

-- Finance compares this view with the mainframe PRMMONTH summary for UK lines every month.
CREATE OR REPLACE VIEW dw.v_premium_by_line AS
SELECT line_code,
       region,
       currency,
       date_trunc('month', bill_date)::date AS bill_month,
       COUNT(*)                            AS policies_billed,
       SUM(premium_amt)                    AS premium_total,
       SUM(ipt_amt)                        AS ipt_total
FROM dw.premium_billing
GROUP BY line_code, region, currency, date_trunc('month', bill_date);

-- Refreshed by the last task of the Airflow DAG premium_billing_load (REFRESH ... CONCURRENTLY needs the
-- unique index below). Read by the finance dashboards.
CREATE MATERIALIZED VIEW dw.mv_premium_by_line_month AS
SELECT * FROM dw.v_premium_by_line;
CREATE UNIQUE INDEX ux_mv_premium_by_line_month
    ON dw.mv_premium_by_line_month(line_code, region, currency, bill_month);

-- Upserted by warehouse-loader closed_claims for each claims.closed.v1 event (loss-ratio reporting).
CREATE TABLE dw.claim_closed_fact (
    claim_id          uuid PRIMARY KEY,
    policy_number     varchar(12) NOT NULL,
    line_code         char(3) NOT NULL,
    closed_on         date NOT NULL,
    paid_amount       numeric(12,2) NOT NULL,
    reserve_released  numeric(12,2) NOT NULL DEFAULT 0,
    currency          char(3) NOT NULL,
    loaded_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_claim_closed_fact_line ON dw.claim_closed_fact(line_code, closed_on);
