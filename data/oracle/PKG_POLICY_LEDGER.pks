CREATE OR REPLACE PACKAGE LEDGER.PKG_POLICY_LEDGER AS
    -- Posting API for policy-admin (LedgerClient). One call per bound policy.

    E_UNKNOWN_LINE EXCEPTION;
    PRAGMA EXCEPTION_INIT(E_UNKNOWN_LINE, -20001);

    PROCEDURE post_premium (
        p_policy_no   IN  VARCHAR2,
        p_party_ref   IN  VARCHAR2,
        p_line_code   IN  CHAR,
        p_premium     IN  NUMBER,
        p_ipt         IN  NUMBER,
        p_currency    IN  CHAR,
        p_effective   IN  DATE,
        p_posting_id  OUT NUMBER
    );

    PROCEDURE post_refund (
        p_policy_no   IN  VARCHAR2,
        p_amount      IN  NUMBER,
        p_effective   IN  DATE
    );

    FUNCTION balance_of (p_policy_no IN VARCHAR2) RETURN NUMBER;
END PKG_POLICY_LEDGER;
/
