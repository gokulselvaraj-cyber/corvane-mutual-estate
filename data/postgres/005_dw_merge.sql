-- dw.fn_merge_billing: moves one staged billing file into dw.premium_billing and returns the number of
-- rows merged. Called by warehouse-loader load_billing_file after staging. Re-running a load is safe:
-- rows are upserted on (policy_no, line_code, bill_date).

CREATE OR REPLACE FUNCTION dw.fn_merge_billing(p_load_id bigint)
RETURNS integer
LANGUAGE plpgsql AS $$
DECLARE
    staged   integer;
    expected integer;
    merged   integer;
BEGIN
    SELECT record_count INTO expected FROM dw.billing_load WHERE load_id = p_load_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'billing load % not found', p_load_id;
    END IF;
    SELECT COUNT(*) INTO staged FROM dw.premium_billing_stage WHERE load_id = p_load_id;
    IF staged <> expected THEN
        UPDATE dw.billing_load
           SET status = 'REJECTED',
               rejected_reason = format('staged %s rows, file had %s records', staged, expected)
         WHERE load_id = p_load_id;
        RETURN 0;
    END IF;

    INSERT INTO dw.premium_billing AS t
          (policy_no, line_code, bill_date, premium_amt, ipt_amt, currency, region, load_id)
    SELECT policy_no, line_code, bill_date, premium_amt, ipt_amt, currency, region, load_id
      FROM dw.premium_billing_stage
     WHERE load_id = p_load_id
    ON CONFLICT (policy_no, line_code, bill_date) DO UPDATE
       SET premium_amt = EXCLUDED.premium_amt,
           ipt_amt     = EXCLUDED.ipt_amt,
           load_id     = EXCLUDED.load_id,
           loaded_at   = now();
    GET DIAGNOSTICS merged = ROW_COUNT;

    UPDATE dw.billing_load SET status = 'MERGED' WHERE load_id = p_load_id;
    DELETE FROM dw.premium_billing_stage WHERE load_id = p_load_id;
    RETURN merged;
END $$;
