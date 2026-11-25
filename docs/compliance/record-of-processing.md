# Record of processing activities (UK GDPR Article 30)

**Controller:** Corvane Mutual Insurance. **Owner:** platform architecture, with the Data Protection Officer.
**Last reviewed:** 2026-09-30. Review yearly or when a new system processes personal data.

## Processing activities

| Activity | Systems | Personal data | Lawful basis | Processors |
|---|---|---|---|---|
| First notice of loss (FNOL) | customer-portal, claims-service, claimsdb (`claims.claim`, `claims.claim_party`) | Name, date of birth, NI number or SSN, contact details, address, photos, **injury notes** | Contract; special-category data under the insurance condition (DPA 2018 Sch. 1 para 20) | None |
| Fraud triage | fraud-scoring, AI gateway | Claimant name, postcode, narrative, **injury notes** | Legitimate interests (fraud prevention) | AI gateway provider (DPA-2025-07) |
| Claim payouts | payments-gateway, ClearRiver Bank Payouts | Payee name, sort code, account number | Contract | ClearRiver Bank |
| Notifications | notifications, SMTP relay, TextWave SMS | Name, email, mobile number | Contract | TextWave |
| Reporting warehouse | warehouse-loader, `dw` schema | Policy numbers, premiums; claims events (no injury notes) | Legitimate interests (financial reporting) | None |
| Reinsurance bordereaux | mainframe RIBORDX | Policy and claim numbers only | Legal obligation / contract with reinsurers | Reinsurance broker |

Injury notes are special-category data. Sending them to the AI gateway for fraud triage needs a DPIA:
**DPIA-14 is pending** and the triage flag must stay off until it is signed.

## Retention schedule

| Record | Kept for | Enforced by |
|---|---|---|
| Claims and claim parties | 7 years after the claim is closed | `claims.purge_expired_claims()` |
| Claim audit history | To be confirmed | Not yet agreed with Legal |
| Claim documents and photos | With the claim | Bucket lifecycle |
| Policy records | 7 years after the policy ends | policy-admin archive job |
| Call recordings | 2 years | Telephony platform |

## International transfers

None. All Corvane customer personal data is stored and processed in the UK (GCP europe-west2). US-written
business is held by the US fronting carrier under its own controllership.

## Data subject rights

Requests go to the DPO mailbox and are logged in the privacy case tool. Subject access requests are answered
within one month; claims data is exported from claimsdb by the claims-platform team.
