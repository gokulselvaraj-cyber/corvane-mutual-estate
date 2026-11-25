# Capability map

| Level 1 | Level 2 capability | Systems |
|---|---|---|
| Sell | Quote and rate | customer-portal, policy-admin, mainframe PRMCALC0 |
| Sell | Bind and issue | policy-admin, Oracle LEDGER |
| Sell | Broker distribution and commission | broker-commissions |
| Service | Policy view and changes | customer-portal, policy-admin |
| Service | Premium billing | mainframe PRMNIGHT, warehouse-loader |
| Claims | First notice of loss | customer-portal, claims-service |
| Claims | Fraud detection | fraud-scoring, Sentinel Claims Exchange |
| Claims | Field assessment | adjuster-app, claims-service |
| Claims | Settlement and payout | claims-service, payments-gateway, ClearRiver Bank |
| Claims | Claims inquiry (call centre) | CICS CLMI, claims-service summary API |
| Claims | Subrogation and recovery | **planned 2027, not built** |
| Communicate | Customer notifications | notifications |
| Insight | Premium and claims reporting | warehouse (dw schema) |
