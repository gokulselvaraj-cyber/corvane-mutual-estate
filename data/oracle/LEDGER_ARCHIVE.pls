-- LEDGER_ARCHIVE: moved postings older than 7 years to LEDGER.PREMIUM_POSTING_ARCH.
-- Written 2019. NOT DEPLOYED since 2022, when PREMIUM_POSTING became interval-partitioned and old partitions are
-- dropped by the DBA job instead. Kept for audit reference only.
CREATE OR REPLACE PROCEDURE LEDGER.LEDGER_ARCHIVE (p_before IN DATE DEFAULT ADD_MONTHS(TRUNC(SYSDATE), -84)) AS
    CURSOR c_old IS
        SELECT POSTING_ID FROM LEDGER.PREMIUM_POSTING WHERE EFFECTIVE_DATE < p_before FOR UPDATE SKIP LOCKED;
    v_moved PLS_INTEGER := 0;
BEGIN
    FOR r IN c_old LOOP
        INSERT INTO LEDGER.PREMIUM_POSTING_ARCH SELECT * FROM LEDGER.PREMIUM_POSTING WHERE POSTING_ID = r.POSTING_ID;
        DELETE FROM LEDGER.PREMIUM_POSTING WHERE CURRENT OF c_old;
        v_moved := v_moved + 1;
        IF MOD(v_moved, 5000) = 0 THEN
            COMMIT;
        END IF;
    END LOOP;
    COMMIT;
    DBMS_OUTPUT.PUT_LINE('Archived ' || v_moved || ' postings before ' || TO_CHAR(p_before, 'YYYY-MM-DD'));
END LEDGER_ARCHIVE;
/
