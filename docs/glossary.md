# Glossary

| Term | Meaning | Also called |
|---|---|---|
| Policyholder | The person or company who owns a policy | **Customer** (portal), **PolicyHolder** (policy-admin), **INSURED** (mainframe POLREC), **PARTY** (Oracle ledger), `claim_party` with role `policyholder` (claims database) |
| Claim | A request by a policyholder to be paid for a loss | Not to be confused with a token *claim* (a field inside a JWT) |
| Policy | An insurance contract | Not to be confused with an access-control policy in claims-service security code |
| Reserve | Money set aside for the expected cost of a claim | Not the same as a reserved appointment slot in the adjuster app |
| Excess | The part of a claim the policyholder pays | Deductible (US) |
| FNOL | First notice of loss: the first report of a claim | |
| IPT | Insurance premium tax (UK): 12% standard, 20% higher rate | |
| CLMI | The CICS claims inquiry transaction | |
| PRMNIGHT | The nightly premium billing batch job | |
| Claimant | The person making the claim; usually the policyholder, but a THIRD_PARTY in liability claims (PLB, motor third-party) | **Not** a synonym of policyholder |
