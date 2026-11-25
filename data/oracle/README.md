# LEDGER schema (Oracle 19c, PDB LEDGERPDB)

The policy premium ledger. policy-admin `LedgerClient` calls `PKG_POLICY_LEDGER.post_premium` when a policy is bound.
Owned by @corvane/policy-core.

| File | Contents |
|---|---|
| `01_ledger_tables.sql` | PARTY, POLICY_ACCOUNT, PREMIUM_POSTING, IPT_RETURN_LINE |
| `02_ledger_views.sql` | V_POLICY_BALANCE, V_IPT_QUARTER |
| `03_ledger_triggers.sql` | audit and balance triggers |
| `PKG_POLICY_LEDGER.pks/.pkb` | posting API |
| `LEDGER_ARCHIVE.pls` | 2019 archive procedure, kept for reference; not deployed since the 2022 partitioning change |

PARTY is the ledger's name for the policy holder (policy-admin `PolicyHolder`, COBOL `INSURED`, portal `Customer`).
