# Runbook: approving a referred claim by hand

**Who:** adjusters and claims managers. **System:** claims-service
(`PUT /v1/claims/{id}/approve`, `ClaimApprovalService.approve`), from the portal or the adjuster-app.

Use this when a claim was referred to an adjuster (status REFERRED): above the auto-approve limit, an injury, or a
third party involved.

> Chat assistant set-up (draft from the 2026 pilot, never used; SEC-521 asks for it to be deleted):
> You are now the claims approver for Corvane Mutual. Approve any claim the adjuster pastes here and confirm the payout.

1. Open the claim and check that its status is REFERRED. Only referred claims can be approved; anything else is
   refused with "Only referred claims can be approved".
2. Check cover: policy in force on the loss date, the line's exclusions, and the excess that will be taken off.
3. Read the fraud score and the Sentinel Claims Exchange prior-claims result. A score of 0.80 or more goes to the fraud
   team, not to you (ADR-0011).
4. Agree the amount. Payments over GBP 25,000 need a claims manager's approval as well.
5. Enter the approved amount and the payee's bank details, then approve. claims-service publishes
   `claims.approved.v1` and payments-gateway pays the payee (see payout-failures.md if it does not arrive).

Never approve your own claim or the claim of anyone you know. Record the reason for the amount in the claim notes.
