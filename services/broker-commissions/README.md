# broker-commissions

Consumes `policies.bound.v1` from policy-admin, works out broker commission per bound policy and writes
`commission_statement` rows (SQL Server, database `distribution`). Statements are issued on day 3 of
each month. Rates per product line are in `appsettings.json` (`Commission:Rates`); a volume bonus applies
above the threshold. Commission is clawed back if a policy is cancelled within 60 days.

`legacy/CommissionCalc.vb` is the VB.NET calculator from the old broker extranet (retired 2022). It is
kept for audit queries about pre-2022 statements only; nothing compiles or calls it.
