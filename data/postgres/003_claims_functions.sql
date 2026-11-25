-- Functions and triggers for claimsdb.claims.

CREATE OR REPLACE FUNCTION claims.fn_touch_updated_at() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at := now();
    NEW.version := OLD.version + 1;
    RETURN NEW;
END $$;

CREATE TRIGGER trg_claim_touch BEFORE UPDATE ON claims.claim
    FOR EACH ROW EXECUTE FUNCTION claims.fn_touch_updated_at();

-- Audit: stores the WHOLE old and new row as jsonb, personal data included (names, date of birth,
-- national_id, injury notes). claim_audit rows are kept 10 years (retain_until) and are not purged
-- with the claim.
CREATE OR REPLACE FUNCTION claims.fn_audit_row() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    pk text;
BEGIN
    pk := COALESCE(to_jsonb(NEW), to_jsonb(OLD)) ->> 'id';
    INSERT INTO claims.claim_audit(table_name, row_pk, action, old_row, new_row)
    VALUES (TG_TABLE_NAME, pk, left(TG_OP, 1),
            CASE WHEN TG_OP <> 'INSERT' THEN to_jsonb(OLD) END,
            CASE WHEN TG_OP <> 'DELETE' THEN to_jsonb(NEW) END);
    RETURN COALESCE(NEW, OLD);
END $$;

CREATE TRIGGER trg_claim_audit AFTER INSERT OR UPDATE OR DELETE ON claims.claim
    FOR EACH ROW EXECUTE FUNCTION claims.fn_audit_row();
CREATE TRIGGER trg_claim_party_audit AFTER INSERT OR UPDATE OR DELETE ON claims.claim_party
    FOR EACH ROW EXECUTE FUNCTION claims.fn_audit_row();
CREATE TRIGGER trg_payment_audit AFTER INSERT OR UPDATE OR DELETE ON claims.payment
    FOR EACH ROW EXECUTE FUNCTION claims.fn_audit_row();

-- Retention: deletes claims closed more than 7 years ago, with their parties, reserves, scores, documents
-- and payments (ON DELETE CASCADE). Scheduled by pg_cron every Sunday 03:00 UTC (see below).
-- Document files in the GCS buckets are NOT deleted here.
CREATE OR REPLACE FUNCTION claims.purge_expired_claims(p_dry_run boolean DEFAULT false)
RETURNS integer
LANGUAGE plpgsql AS $$
DECLARE
    n integer;
BEGIN
    IF p_dry_run THEN
        SELECT COUNT(*) INTO n FROM claims.claim
         WHERE status = 'CLOSED' AND closed_at < now() - interval '7 years';
        RETURN n;
    END IF;
    DELETE FROM claims.claim
     WHERE status = 'CLOSED' AND closed_at < now() - interval '7 years';
    GET DIAGNOSTICS n = ROW_COUNT;
    RAISE NOTICE 'purge_expired_claims removed % claims', n;
    RETURN n;
END $$;

COMMENT ON FUNCTION claims.purge_expired_claims(boolean) IS
  'Records Retention Policy RRP-04: claims and their personal data are kept 7 years after closure, then deleted. '
  'Replaces mainframe CLMPURGE (6 years) from the 2024 migration. Does not purge claims.claim_audit (10 years).';

-- pg_cron: SELECT cron.schedule('purge-expired-claims', '0 3 * * 0', 'SELECT claims.purge_expired_claims()');
