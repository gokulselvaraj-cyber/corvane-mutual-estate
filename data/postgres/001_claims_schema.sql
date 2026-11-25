-- claimsdb, schema claims: the system of record for claims since the 2024 migration off CORV.CLMMAST.
-- Owner: @corvane/claims-platform. PostgreSQL 15.
-- Writers: claims-service (JPA entities Claim, ClaimParty), payments-gateway (claims.payment),
-- fraud-scoring (claims.fraud_score), scripts/oneoff/backfill_2023_reserves.py (claims.claim_reserve).

CREATE SCHEMA IF NOT EXISTS claims;

-- ClaimRepository.nextClaimNumber(): claim numbers are 'CLM' || line code || lpad(nextval, 8).
CREATE SEQUENCE claims.claim_number_seq START WITH 10000001 INCREMENT BY 1 CACHE 20;

CREATE TABLE claims.claim (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_number        varchar(14)  NOT NULL UNIQUE,
    policy_number       varchar(12)  NOT NULL,
    line_code           char(3)      NOT NULL CHECK (line_code IN
                          ('MTR','HOM','CNT','TRV','PET','LLD','MAR','CPR','PLB','PIN','CYB','GDG')),
    status              varchar(12)  NOT NULL DEFAULT 'REGISTERED' CHECK (status IN
                          ('REGISTERED','REFERRED','APPROVED','PAID','CLOSED','DECLINED','REOPENED')),
    triage_outcome      varchar(20),            -- AUTO_APPROVED, ADJUSTER or REFER_FRAUD (TriageService)
    incident_date       date         NOT NULL,
    loss_cause          varchar(6)   NOT NULL,
    description         text,
    injury_notes        text,
    estimated_amount    numeric(12,2) NOT NULL,
    reserve_amount      numeric(12,2) NOT NULL DEFAULT 0,
    excess_amount       numeric(9,2)  NOT NULL DEFAULT 0,
    paid_amount         numeric(12,2) NOT NULL DEFAULT 0,
    fraud_score         numeric(4,3)  CHECK (fraud_score BETWEEN 0 AND 1),
    adjuster_id         varchar(8),
    currency            char(3)      NOT NULL DEFAULT 'GBP',
    region              char(2)      NOT NULL DEFAULT 'UK' CHECK (region IN ('UK','US')),
    registered_at       timestamptz  NOT NULL DEFAULT now(),
    registered_by       varchar(64)  NOT NULL,
    reported_at         timestamptz  GENERATED ALWAYS AS (registered_at) STORED,  -- old claims-v1 name
    closed_at           timestamptz,
    legacy_reserve_text varchar(40),            -- claims-v1 kept reserves as text, e.g. 'GBP 1,250.00'
    updated_at          timestamptz  NOT NULL DEFAULT now(),
    version             integer      NOT NULL DEFAULT 0
);
COMMENT ON TABLE claims.claim IS 'One row per insurance claim. Retention: 7 years after closed_at, enforced by claims.purge_expired_claims().';
COMMENT ON COLUMN claims.claim.injury_notes IS 'Personal data (health). Free text typed by the claimant at FNOL; also sent to fraud-scoring.';
COMMENT ON COLUMN claims.claim.fraud_score IS 'Latest score from fraud-scoring POST /v1/score; history in claims.fraud_score. Refer above 0.72.';
COMMENT ON COLUMN claims.claim.legacy_reserve_text IS 'Only set on 2023 claims migrated from retired claims-v1. Read once by scripts/oneoff/backfill_2023_reserves.py.';

-- The people on a claim. role = POLICYHOLDER is the same person as PolicyHolder (policy-admin),
-- INSURED (mainframe POLREC), PARTY (Oracle LEDGER) and Customer (customer-portal).
CREATE TABLE claims.claim_party (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id       uuid NOT NULL REFERENCES claims.claim(id) ON DELETE CASCADE,
    role           varchar(12) NOT NULL CHECK (role IN ('POLICYHOLDER','THIRD_PARTY','WITNESS','PAYEE')),
    full_name      varchar(120) NOT NULL,
    date_of_birth  date,
    national_id    varchar(11),
    email          varchar(254),
    phone          varchar(20),
    address_line1  varchar(120),
    town           varchar(60),
    postcode       varchar(10),
    country        char(2) NOT NULL DEFAULT 'GB'
);
COMMENT ON TABLE claims.claim_party IS 'Personal data: name, date of birth, national_id (UK NI number or US SSN), contact details, address.';
CREATE INDEX ix_claim_party_claim ON claims.claim_party(claim_id);
CREATE UNIQUE INDEX ux_claim_party_holder ON claims.claim_party(claim_id) WHERE role = 'POLICYHOLDER';

CREATE TABLE claims.claim_reserve (
    id            bigserial PRIMARY KEY,
    claim_id      uuid NOT NULL REFERENCES claims.claim(id) ON DELETE CASCADE,
    reserve_type  varchar(10) NOT NULL CHECK (reserve_type IN ('INDEMNITY','EXPENSE','RECOVERY')),
    amount        numeric(12,2) NOT NULL,
    currency      char(3) NOT NULL DEFAULT 'GBP',
    reason        varchar(200),
    set_by        varchar(64) NOT NULL,
    set_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_claim_reserve_claim ON claims.claim_reserve(claim_id, set_at DESC);

-- Written by fraud-scoring (store.py) for every claims.registered.v1 event; one row per claim, upserted.
CREATE TABLE claims.fraud_score (
    claim_id       uuid PRIMARY KEY REFERENCES claims.claim(id) ON DELETE CASCADE,
    score          numeric(4,3) NOT NULL CHECK (score BETWEEN 0 AND 1),
    decision       varchar(10) NOT NULL CHECK (decision IN ('CLEAR','REFER','DECLINE')),
    indicators     jsonb NOT NULL DEFAULT '[]',
    llm_label      varchar(40),             -- set only when fraud.llm-triage.enabled
    model_version  varchar(20) NOT NULL,
    scored_at      timestamptz NOT NULL DEFAULT now()
);

-- Written by payments-gateway (internal/store). idempotency_key = claim id + ':' + approval sequence,
-- so a redelivered claims.approved.v1 event never pays twice.
CREATE TABLE claims.payment (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    idempotency_key   varchar(80) NOT NULL,
    claim_id          uuid NOT NULL REFERENCES claims.claim(id) ON DELETE CASCADE,
    amount            numeric(12,2) NOT NULL CHECK (amount > 0),
    currency          char(3) NOT NULL,
    status            varchar(10) NOT NULL CHECK (status IN ('PENDING','SENT','SETTLED','FAILED')),
    provider          varchar(16) NOT NULL DEFAULT 'CLEARRIVER',
    bank_reference    varchar(40),
    failure_reason    varchar(200),
    created_at        timestamptz NOT NULL DEFAULT now(),
    settled_at        timestamptz,
    CONSTRAINT uq_payment_idempotency UNIQUE (idempotency_key)
);
CREATE INDEX ix_payment_claim ON claims.payment(claim_id);
CREATE INDEX ix_payment_open ON claims.payment(status) WHERE status IN ('PENDING','SENT');

-- Files uploaded at FNOL (photos, estimates). Stored by claims-service GcsDocumentStore in bucket
-- corvane-claims-docs (europe-west2). Terraform replicates that bucket to corvane-claims-docs-dr in us-east1.
CREATE TABLE claims.claim_document (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id      uuid NOT NULL REFERENCES claims.claim(id) ON DELETE CASCADE,
    kind          varchar(12) NOT NULL CHECK (kind IN ('PHOTO','ESTIMATE','INVOICE','LETTER','MEDICAL')),
    gcs_uri       varchar(300) NOT NULL,
    content_type  varchar(80) NOT NULL,
    size_bytes    bigint NOT NULL,
    uploaded_by   varchar(64) NOT NULL,
    uploaded_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_claim_document_claim ON claims.claim_document(claim_id);

CREATE TABLE claims.claim_audit (
    id            bigserial PRIMARY KEY,
    table_name    varchar(40) NOT NULL,
    row_pk        varchar(64) NOT NULL,
    action        char(1) NOT NULL CHECK (action IN ('I','U','D')),
    old_row       jsonb,
    new_row       jsonb,
    changed_by    varchar(64) NOT NULL DEFAULT current_user,
    changed_at    timestamptz NOT NULL DEFAULT now(),
    retain_until  date NOT NULL DEFAULT (now() + interval '10 years')::date
);
COMMENT ON TABLE claims.claim_audit IS 'Full before/after rows of claim, claim_party and payment, kept 10 years. Not touched by purge_expired_claims().';
CREATE INDEX ix_claim_audit_row ON claims.claim_audit(table_name, row_pk);

CREATE INDEX ix_claim_policy ON claims.claim(policy_number);
CREATE INDEX ix_claim_open ON claims.claim(status) WHERE status NOT IN ('CLOSED','DECLINED');
CREATE INDEX ix_claim_closed ON claims.claim(closed_at) WHERE status = 'CLOSED';
