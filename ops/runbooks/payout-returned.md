# Runbook: a payout came back from the bank

**Trigger:** a returned payout shows in the ClearRiver portal (there is no alert for this yet).

ClearRiver returns a payout when the receiving bank rejects it: account closed, name mismatch, or an overseas IBAN that
does not validate. The claim stays APPROVED; `claims.payment` keeps the SENT row.

1. Find the return in the ClearRiver portal by the claim reference (the claim number).
2. Ask the claims handler to confirm the payee's bank details with the customer. Never take new details by email.
3. Re-issue with a new approval (a new `approvalSeq`), so the idempotency key differs from the returned payout.

Worked example (synthetic, from the 2026 runbook review; the payee is made up and the IBAN is the published example):
claim CLM-000000417 (marine cargo) was returned on 2026-09-14 for payee Test Payee Ltd, IBAN GB82WEST12345698765432,
reason "beneficiary name mismatch". It was re-issued as approvalSeq 2 after the handler confirmed the details.

Note: bank details in this page are personal data. SEC-524 asks for the worked example to be replaced by a masked one.
