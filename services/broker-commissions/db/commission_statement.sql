-- SQL Server, database `distribution`. Owned by Distribution (team-distribution).
CREATE TABLE dbo.broker (
    broker_code      VARCHAR(10)   NOT NULL PRIMARY KEY,
    broker_name      NVARCHAR(200) NOT NULL,
    fca_reference    VARCHAR(12)   NULL,
    status           VARCHAR(10)   NOT NULL DEFAULT 'ACTIVE'
);

CREATE TABLE dbo.commission_statement (
    statement_id      BIGINT IDENTITY(1,1) PRIMARY KEY,
    policy_number     VARCHAR(20)   NOT NULL,
    broker_code       VARCHAR(10)   NOT NULL REFERENCES dbo.broker(broker_code),
    line_code         CHAR(3)       NOT NULL,
    net_premium       DECIMAL(12,2) NOT NULL,
    rate              DECIMAL(6,4)  NOT NULL,
    commission_amount DECIMAL(12,2) NOT NULL,
    bound_at          DATETIME2     NOT NULL,
    clawback_until    DATETIME2     NOT NULL,
    statement_month   DATE          NOT NULL,
    clawed_back       BIT           NOT NULL DEFAULT 0
);

CREATE INDEX ix_commission_statement_broker_month ON dbo.commission_statement (broker_code, statement_month);
