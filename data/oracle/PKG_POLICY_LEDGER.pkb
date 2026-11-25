CREATE OR REPLACE PACKAGE BODY LEDGER.PKG_POLICY_LEDGER AS

    c_lines CONSTANT VARCHAR2(60) := 'MTR,HOM,CNT,TRV,PET,LLD,MAR,CPR,PLB,PIN,CYB,GDG';

    FUNCTION party_id_for (p_party_ref IN VARCHAR2) RETURN NUMBER IS
        v_id LEDGER.PARTY.PARTY_ID%TYPE;
    BEGIN
        SELECT PARTY_ID INTO v_id FROM LEDGER.PARTY WHERE PARTY_REF = p_party_ref;
        RETURN v_id;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            -- First posting for this holder: create the PARTY with a placeholder name; the nightly party sync
            -- from policy-admin fills DISPLAY_NAME.
            INSERT INTO LEDGER.PARTY (PARTY_REF, DISPLAY_NAME) VALUES (p_party_ref, '(pending sync)')
            RETURNING PARTY_ID INTO v_id;
            RETURN v_id;
    END party_id_for;

    FUNCTION account_for (p_policy_no IN VARCHAR2, p_party_id IN NUMBER, p_line IN CHAR,
                          p_currency IN CHAR, p_effective IN DATE) RETURN NUMBER IS
        v_id LEDGER.POLICY_ACCOUNT.ACCOUNT_ID%TYPE;
    BEGIN
        SELECT ACCOUNT_ID INTO v_id FROM LEDGER.POLICY_ACCOUNT WHERE POLICY_NO = p_policy_no;
        RETURN v_id;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            INSERT INTO LEDGER.POLICY_ACCOUNT (POLICY_NO, PARTY_ID, LINE_CODE, CURRENCY, OPENED_ON)
            VALUES (p_policy_no, p_party_id, p_line, p_currency, p_effective)
            RETURNING ACCOUNT_ID INTO v_id;
            RETURN v_id;
    END account_for;

    PROCEDURE post_premium (
        p_policy_no IN VARCHAR2, p_party_ref IN VARCHAR2, p_line_code IN CHAR, p_premium IN NUMBER,
        p_ipt IN NUMBER, p_currency IN CHAR, p_effective IN DATE, p_posting_id OUT NUMBER
    ) IS
        v_account NUMBER;
    BEGIN
        IF INSTR(c_lines, p_line_code) = 0 THEN
            RAISE_APPLICATION_ERROR(-20001, 'Unknown line code ' || p_line_code);
        END IF;
        v_account := account_for(p_policy_no, party_id_for(p_party_ref), p_line_code, p_currency, p_effective);
        INSERT INTO LEDGER.PREMIUM_POSTING (ACCOUNT_ID, POSTING_TYPE, AMOUNT, EFFECTIVE_DATE)
        VALUES (v_account, 'PREMIUM', p_premium - p_ipt, p_effective)
        RETURNING POSTING_ID INTO p_posting_id;
        IF p_ipt > 0 THEN
            INSERT INTO LEDGER.PREMIUM_POSTING (ACCOUNT_ID, POSTING_TYPE, AMOUNT, EFFECTIVE_DATE)
            VALUES (v_account, 'IPT', p_ipt, p_effective);
        END IF;
    END post_premium;

    PROCEDURE post_refund (p_policy_no IN VARCHAR2, p_amount IN NUMBER, p_effective IN DATE) IS
    BEGIN
        INSERT INTO LEDGER.PREMIUM_POSTING (ACCOUNT_ID, POSTING_TYPE, AMOUNT, EFFECTIVE_DATE)
        SELECT ACCOUNT_ID, 'REFUND', ABS(p_amount), p_effective
          FROM LEDGER.POLICY_ACCOUNT WHERE POLICY_NO = p_policy_no;
        IF SQL%ROWCOUNT = 0 THEN
            RAISE_APPLICATION_ERROR(-20002, 'No ledger account for ' || p_policy_no);
        END IF;
    END post_refund;

    FUNCTION balance_of (p_policy_no IN VARCHAR2) RETURN NUMBER IS
        v_balance NUMBER;
    BEGIN
        SELECT BALANCE INTO v_balance FROM LEDGER.POLICY_ACCOUNT WHERE POLICY_NO = p_policy_no;
        RETURN v_balance;
    END balance_of;

END PKG_POLICY_LEDGER;
/
