-- Views over claimsdb.claims.

-- Same fields as the CICS screen CLMINQM (transaction CLMI, program CLMINQ0), plus the policyholder.
-- Intended for claims-service GET /v1/claims/{id}/summary, the REST replacement for CLMI.
CREATE OR REPLACE VIEW claims.v_claim_summary AS
SELECT c.id                           AS claim_id,
       c.claim_number,
       c.policy_number,
       c.line_code,
       c.status,
       c.incident_date,
       c.loss_cause,
       c.reserve_amount,
       COALESCE(p.paid, 0)            AS settled_amount,
       c.fraud_score,
       (c.fraud_score > 0.72)         AS refer_flag,
       c.adjuster_id,
       h.full_name                    AS policyholder_name,
       c.currency
FROM claims.claim c
LEFT JOIN claims.claim_party h ON h.claim_id = c.id AND h.role = 'POLICYHOLDER'
LEFT JOIN (SELECT claim_id, SUM(amount) AS paid
             FROM claims.payment WHERE status = 'SETTLED' GROUP BY claim_id) p ON p.claim_id = c.id;

CREATE OR REPLACE VIEW claims.v_open_claims_by_adjuster AS
SELECT adjuster_id, line_code, COUNT(*) AS open_claims, SUM(reserve_amount) AS total_reserve
FROM claims.claim
WHERE status IN ('REGISTERED','REFERRED','APPROVED','REOPENED')
GROUP BY adjuster_id, line_code;

-- Nightly feed that keeps CORV.CLMMAST current for the CICS inquiry (CLMREC layout) until CLMI is retired.
CREATE OR REPLACE VIEW claims.v_claim_mainframe_feed AS
SELECT rpad(c.claim_number, 14)                      AS clm_number,
       rpad(c.policy_number, 12)                     AS clm_pol_number,
       c.line_code                                   AS clm_line_code,
       CASE c.status WHEN 'REGISTERED' THEN 'REG' WHEN 'REFERRED' THEN 'TRI'
                     WHEN 'APPROVED' THEN 'APP' WHEN 'PAID' THEN 'PAI'
                     WHEN 'CLOSED' THEN 'CLS' ELSE 'REJ' END AS clm_status,
       to_char(c.incident_date, 'YYYYMMDD')          AS clm_loss_date,
       to_char(c.closed_at, 'YYYYMMDD')              AS clm_closed_date,
       c.reserve_amount, c.paid_amount, c.fraud_score, c.adjuster_id
FROM claims.claim c
WHERE c.updated_at >= now() - interval '2 days';
