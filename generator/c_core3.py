"""Builder C core part 3: broker-commissions (.NET), warehouse-loader, scripts. Run: python3 -I c_core3.py <estate_root>"""
import json
import os
import sys

ROOT = sys.argv[1]
F = {}
B = "services/broker-commissions/"

F[B + "Corvane.Commissions.csproj"] = '''<Project Sdk="Microsoft.NET.Sdk.Worker">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <RootNamespace>Corvane.Commissions</RootNamespace>
    <Version>3.2.1</Version>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Confluent.Kafka" Version="2.4.0" />
    <PackageReference Include="Dapper" Version="2.1.35" />
    <PackageReference Include="Microsoft.Data.SqlClient" Version="5.2.1" />
    <PackageReference Include="Microsoft.Extensions.Hosting" Version="8.0.0" />
  </ItemGroup>
  <ItemGroup>
    <Compile Remove="legacy/**" />
    <Compile Remove="tests/**" />
  </ItemGroup>
</Project>
'''

F[B + "appsettings.json"] = json.dumps({
    "Kafka": {"BootstrapServers": "kafka.corvane.internal:9092", "Topic": "policies.bound.v1",
              "GroupId": "broker-commissions"},
    "ConnectionStrings": {"Commissions": "Server=sql-dist.corvane.internal;Database=distribution;"
                                         "User Id=commissions;Password=${COMMISSIONS_DB_PASSWORD};Encrypt=true"},
    "Commission": {
        "_comment": "Base commission rates by product line, as a fraction of net written premium (excl. IPT).",
        "Rates": {"MTR": 0.12, "HOM": 0.15, "CNT": 0.15, "TRV": 0.20, "PET": 0.18, "LLD": 0.14,
                  "MAR": 0.10, "CPR": 0.125, "PLB": 0.11, "PIN": 0.09, "CYB": 0.08, "GDG": 0.22},
        "VolumeBonus": {"ThresholdGbp": 250000, "ExtraRate": 0.01},
        "ClawbackDays": 60,
        "StatementDay": 3,
    },
    "Logging": {"LogLevel": {"Default": "Information"}},
}, indent=2) + "\n"

F[B + "appsettings.Production.json"] = json.dumps({
    "Kafka": {"BootstrapServers": "kafka-prod-1.corvane.internal:9092,kafka-prod-2.corvane.internal:9092"},
    "ConnectionStrings": {"Commissions": "Server=sql-dist-prod.corvane.internal;Database=distribution;"
                                         "User Id=commissions;Password=${COMMISSIONS_DB_PASSWORD};Encrypt=true"},
    "Commission": {"VolumeBonus": {"ThresholdGbp": 300000, "ExtraRate": 0.0125}},
}, indent=2) + "\n"

F[B + "Dockerfile"] = '''FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY . .
RUN dotnet publish Corvane.Commissions.csproj -c Release -o /out

FROM mcr.microsoft.com/dotnet/runtime:8.0
WORKDIR /app
COPY --from=build /out .
USER app
ENTRYPOINT ["dotnet", "Corvane.Commissions.dll"]
'''

F[B + "catalog-info.yaml"] = '''apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: broker-commissions
  description: Calculates broker commission on bound policies and produces monthly statements.
spec:
  type: service
  lifecycle: production
  owner: team-distribution
  system: corvane-distribution
  dependsOn: [resource:kafka-policy, resource:sql-distribution]
'''

F[B + "build.ps1"] = '''# Local build and test for broker-commissions (Windows developer machines).
param([string]$Configuration = "Release")
$ErrorActionPreference = "Stop"
dotnet restore Corvane.Commissions.csproj
dotnet build Corvane.Commissions.csproj -c $Configuration --no-restore
dotnet test tests/Corvane.Commissions.Tests.csproj -c $Configuration
Write-Host "broker-commissions built ($Configuration)"
'''

F[B + "README.md"] = '''# broker-commissions

Consumes `policies.bound.v1` from policy-admin, works out broker commission per bound policy and writes
`commission_statement` rows (SQL Server, database `distribution`). Statements are issued on day 3 of
each month. Rates per product line are in `appsettings.json` (`Commission:Rates`); a volume bonus applies
above the threshold. Commission is clawed back if a policy is cancelled within 60 days.

`legacy/CommissionCalc.vb` is the VB.NET calculator from the old broker extranet (retired 2022). It is
kept for audit queries about pre-2022 statements only; nothing compiles or calls it.
'''

F[B + "src/Program.cs"] = '''using Corvane.Commissions.Calculation;
using Corvane.Commissions.Consumers;
using Corvane.Commissions.Data;

var builder = Host.CreateApplicationBuilder(args);
builder.Services.Configure<CommissionOptions>(builder.Configuration.GetSection("Commission"));
builder.Services.AddSingleton<CommissionCalculator>();
builder.Services.AddSingleton<StatementRepository>();
builder.Services.AddHostedService<BoundPolicyConsumer>();
builder.Build().Run();
'''

F[B + "src/Calculation/CommissionOptions.cs"] = '''namespace Corvane.Commissions.Calculation;

public sealed class CommissionOptions
{
    public Dictionary<string, decimal> Rates { get; set; } = new();
    public VolumeBonusOptions VolumeBonus { get; set; } = new();
    public int ClawbackDays { get; set; } = 60;
    public int StatementDay { get; set; } = 3;
}

public sealed class VolumeBonusOptions
{
    public decimal ThresholdGbp { get; set; }
    public decimal ExtraRate { get; set; }
}
'''

F[B + "src/Calculation/CommissionCalculator.cs"] = '''using Corvane.Commissions.Rules;
using Microsoft.Extensions.Options;

namespace Corvane.Commissions.Calculation;

/// <summary>Works out broker commission for one bound policy (journey J6).</summary>
public sealed class CommissionCalculator
{
    private readonly CommissionOptions _options;

    public CommissionCalculator(IOptions<CommissionOptions> options) => _options = options.Value;

    public CommissionLine Calculate(BoundPolicy policy, decimal brokerYearToDateGwp)
    {
        if (!_options.Rates.TryGetValue(policy.LineCode, out var rate))
            throw new InvalidOperationException($"No commission rate for line {policy.LineCode}");

        // Commission is on net premium: insurance premium tax is never commissionable.
        var net = policy.GrossPremium - policy.IptAmount;
        var lineRule = LineCommissionRules.For(policy.LineCode);
        var adjustedRate = lineRule.AdjustRate(rate, policy);

        if (brokerYearToDateGwp >= _options.VolumeBonus.ThresholdGbp)
            adjustedRate += _options.VolumeBonus.ExtraRate;

        var amount = Math.Round(net * adjustedRate, 2, MidpointRounding.ToEven);
        return new CommissionLine(policy.PolicyNumber, policy.BrokerCode, policy.LineCode, net, adjustedRate,
                                  amount, policy.BoundAt.AddDays(_options.ClawbackDays));
    }
}

public sealed record BoundPolicy(string PolicyNumber, string BrokerCode, string LineCode, decimal GrossPremium,
                                 decimal IptAmount, string Currency, DateTime BoundAt, IReadOnlyDictionary<string, string> Attributes);

public sealed record CommissionLine(string PolicyNumber, string BrokerCode, string LineCode, decimal NetPremium,
                                    decimal Rate, decimal Amount, DateTime ClawbackUntil);
'''

F[B + "src/Consumers/BoundPolicyConsumer.cs"] = '''using System.Text.Json;
using Confluent.Kafka;
using Corvane.Commissions.Calculation;
using Corvane.Commissions.Data;

namespace Corvane.Commissions.Consumers;

/// <summary>Reads policies.bound.v1 (published by policy-admin PolicyService.bind).</summary>
public sealed class BoundPolicyConsumer : BackgroundService
{
    private readonly IConfiguration _config;
    private readonly CommissionCalculator _calculator;
    private readonly StatementRepository _repo;
    private readonly ILogger<BoundPolicyConsumer> _log;

    public BoundPolicyConsumer(IConfiguration config, CommissionCalculator calculator, StatementRepository repo,
                               ILogger<BoundPolicyConsumer> log)
    {
        _config = config; _calculator = calculator; _repo = repo; _log = log;
    }

    protected override Task ExecuteAsync(CancellationToken stoppingToken) => Task.Run(() =>
    {
        var cfg = new ConsumerConfig
        {
            BootstrapServers = _config["Kafka:BootstrapServers"],
            GroupId = _config["Kafka:GroupId"],
            EnableAutoCommit = false,
            AutoOffsetReset = AutoOffsetReset.Earliest,
        };
        using var consumer = new ConsumerBuilder<string, string>(cfg).Build();
        consumer.Subscribe(_config["Kafka:Topic"]);
        while (!stoppingToken.IsCancellationRequested)
        {
            var result = consumer.Consume(stoppingToken);
            var evt = JsonSerializer.Deserialize<BoundPolicy>(result.Message.Value,
                new JsonSerializerOptions { PropertyNameCaseInsensitive = true })!;
            if (string.IsNullOrEmpty(evt.BrokerCode))
            {
                consumer.Commit(result); // direct business: no commission
                continue;
            }
            var ytd = _repo.BrokerYearToDateGwp(evt.BrokerCode, evt.BoundAt.Year);
            var line = _calculator.Calculate(evt, ytd);
            _repo.Insert(line, evt.BoundAt);
            _log.LogInformation("Commission {Amount} for {Policy} broker {Broker}", line.Amount, line.PolicyNumber, line.BrokerCode);
            consumer.Commit(result);
        }
    }, stoppingToken);
}
'''

F[B + "src/Data/StatementRepository.cs"] = '''using Corvane.Commissions.Calculation;
using Dapper;
using Microsoft.Data.SqlClient;

namespace Corvane.Commissions.Data;

public sealed class StatementRepository
{
    private readonly string _cs;

    public StatementRepository(IConfiguration config) => _cs = config.GetConnectionString("Commissions")!;

    public decimal BrokerYearToDateGwp(string brokerCode, int year)
    {
        using var db = new SqlConnection(_cs);
        return db.ExecuteScalar<decimal?>(
            "SELECT SUM(net_premium) FROM dbo.commission_statement WHERE broker_code = @brokerCode AND YEAR(bound_at) = @year",
            new { brokerCode, year }) ?? 0m;
    }

    public void Insert(CommissionLine line, DateTime boundAt)
    {
        using var db = new SqlConnection(_cs);
        db.Execute(@"INSERT INTO dbo.commission_statement
            (policy_number, broker_code, line_code, net_premium, rate, commission_amount, bound_at, clawback_until, statement_month)
            VALUES (@PolicyNumber, @BrokerCode, @LineCode, @NetPremium, @Rate, @Amount, @boundAt, @ClawbackUntil,
                    DATEFROMPARTS(YEAR(@boundAt), MONTH(@boundAt), 1))",
            new { line.PolicyNumber, line.BrokerCode, line.LineCode, line.NetPremium, line.Rate, line.Amount, boundAt, line.ClawbackUntil });
    }
}
'''

F[B + "db/commission_statement.sql"] = '''-- SQL Server, database `distribution`. Owned by Distribution (team-distribution).
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
'''

F[B + "legacy/CommissionCalc.vb"] = """' Broker extranet commission calculator, VB.NET 2008. RETIRED 2022 - kept for audit of old statements.
' Rates were hard-coded; Motor was 10% until the 2022 rate review moved it into appsettings.
Imports System.Data.SqlClient

Public Class CommissionCalc
    Private Const MOTOR_RATE As Decimal = 0.1D
    Private Const HOME_RATE As Decimal = 0.15D
    Private Const TRAVEL_RATE As Decimal = 0.2D

    Public Function Calculate(ByVal lineCode As String, ByVal grossPremium As Decimal, ByVal ipt As Decimal) As Decimal
        Dim rate As Decimal
        Select Case lineCode
            Case "MTR"
                rate = MOTOR_RATE
            Case "HOM", "CNT"
                rate = HOME_RATE
            Case "TRV"
                rate = TRAVEL_RATE
            Case Else
                rate = 0.1D
        End Select
        ' Bug kept for audit reproducibility: commission was paid on GROSS premium including IPT.
        Return Math.Round(grossPremium * rate, 2)
    End Function
End Class
"""

F[B + "tests/Corvane.Commissions.Tests.csproj"] = '''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup><TargetFramework>net8.0</TargetFramework></PropertyGroup>
  <ItemGroup>
    <PackageReference Include="xunit" Version="2.8.1" />
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.10.0" />
    <ProjectReference Include="../Corvane.Commissions.csproj" />
  </ItemGroup>
</Project>
'''

F[B + "tests/CommissionCalculatorTests.cs"] = '''using Corvane.Commissions.Calculation;
using Microsoft.Extensions.Options;
using Xunit;

namespace Corvane.Commissions.Tests;

public class CommissionCalculatorTests
{
    private static CommissionCalculator Calc() => new(Options.Create(new CommissionOptions
    {
        Rates = new() { ["MTR"] = 0.12m, ["HOM"] = 0.15m, ["GDG"] = 0.22m },
        VolumeBonus = new() { ThresholdGbp = 250000m, ExtraRate = 0.01m },
    }));

    private static BoundPolicy Policy(string line, decimal gross, decimal ipt) =>
        new("P-1", "BRK001", line, gross, ipt, "GBP", new DateTime(2026, 4, 1), new Dictionary<string, string>());

    [Fact]
    public void MotorCommissionIsTwelvePercentOfNetPremium()
    {
        var line = Calc().Calculate(Policy("MTR", 1120m, 120m), 0m);
        Assert.Equal(120.00m, line.Amount);
    }

    [Fact]
    public void VolumeBonusAddsOnePointAboveThreshold()
    {
        var line = Calc().Calculate(Policy("HOM", 1000m, 0m), 300000m);
        Assert.Equal(0.16m, line.Rate);
    }

    [Fact]
    public void UnknownLineIsRejected()
    {
        Assert.Throws<InvalidOperationException>(() => Calc().Calculate(Policy("XYZ", 100m, 0m), 0m));
    }

    [Fact]
    public void ClawbackWindowIsSixtyDays()
    {
        var line = Calc().Calculate(Policy("GDG", 100m, 0m), 0m);
        Assert.Equal(new DateTime(2026, 5, 31), line.ClawbackUntil);
    }
}
'''

W = "services/warehouse-loader/"
F[W + "pyproject.toml"] = '''[project]
name = "corvane-warehouse-loader"
version = "0.14.0"
requires-python = ">=3.11"
dependencies = ["psycopg[binary]==3.1.19", "confluent-kafka==2.4.0"]

[project.optional-dependencies]
test = ["pytest==8.2.2"]
'''

F[W + "loader.ini"] = '''; warehouse-loader runtime settings. Secrets are injected as environment variables.
[warehouse]
dsn = postgresql://loader@claimsdb:5432/claimsdb
password = ${WAREHOUSE_PASSWORD}
stage_table = dw.premium_billing_stage
merge_function = dw.fn_merge_billing

[landing]
billing_dir = /landing/billing
file_pattern = CORV.PRM.BILLING.DAILY.D*.txt
archive_dir = /landing/billing/archive
record_length = 64

[kafka]
bootstrap = kafka.corvane.internal:9092
closed_topic = claims.closed.v1
group = warehouse-loader
'''

F[W + "Dockerfile"] = '''FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml loader.ini ./
COPY corvane_loader ./corvane_loader
RUN pip install --no-cache-dir .
USER 10001
CMD ["python", "-m", "corvane_loader.billing"]
'''

F[W + "Makefile"] = '''# warehouse-loader developer tasks
.PHONY: test lint load-sample

test:
\tpython -m pytest -q tests

lint:
\tpython -m ruff check corvane_loader

load-sample:
\tpython -m corvane_loader.billing --file tests/data/billing_sample.txt --dry-run
'''

F[W + "catalog-info.yaml"] = '''apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: warehouse-loader
  description: Loads the mainframe premium billing file and closed claims into the dw schema.
spec:
  type: service
  lifecycle: production
  owner: team-data-platform
  system: corvane-data
  dependsOn: [resource:claimsdb, resource:kafka-claims]
'''

F[W + "corvane_loader/__init__.py"] = ""

F[W + "corvane_loader/billrec.py"] = '''"""Fixed-width layout of the mainframe BILLREC copybook (mainframe/copybooks/BILLREC.cpy).

    05 POLICY-NO     PIC X(12).          positions  1-12
    05 LINE-CODE     PIC X(3).           positions 13-15
    05 BILL-DATE     PIC 9(8).           positions 16-23   (CCYYMMDD)
    05 PREMIUM-AMT   PIC S9(9)V99.       positions 24-34   (zoned decimal, sign overpunched in last byte)
    05 IPT-AMT       PIC S9(7)V99.       positions 35-43
    05 CURRENCY      PIC X(3).           positions 44-46
    05 REGION        PIC X(2).           positions 47-48
    05 FILLER        PIC X(16).          positions 49-64

The file arrives ASCII (the SFTP step in JCL PRMNIGHT STEP040 converts from EBCDIC).
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

RECORD_LENGTH = 64

# (name, start, length) with 0-based start
FIELDS = (
    ("policy_no", 0, 12),
    ("line_code", 12, 3),
    ("bill_date", 15, 8),
    ("premium_amt", 23, 11),
    ("ipt_amt", 34, 9),
    ("currency", 43, 3),
    ("region", 46, 2),
)

# Zoned-decimal overpunch: last character carries the sign.
_POS = {"{": "0", "A": "1", "B": "2", "C": "3", "D": "4", "E": "5", "F": "6", "G": "7", "H": "8", "I": "9"}
_NEG = {"}": "0", "J": "1", "K": "2", "L": "3", "M": "4", "N": "5", "O": "6", "P": "7", "Q": "8", "R": "9"}


def zoned(text: str, scale: int = 2) -> Decimal:
    last = text[-1]
    sign = 1
    if last in _POS:
        text = text[:-1] + _POS[last]
    elif last in _NEG:
        text = text[:-1] + _NEG[last]
        sign = -1
    return sign * Decimal(text) / (10 ** scale)


@dataclass(frozen=True)
class BillingRecord:
    policy_no: str
    line_code: str
    bill_date: date
    premium_amt: Decimal
    ipt_amt: Decimal
    currency: str
    region: str


def parse(line: str) -> BillingRecord:
    line = line.rstrip("\\r\\n").ljust(RECORD_LENGTH)
    raw = {name: line[start:start + length] for name, start, length in FIELDS}
    d = raw["bill_date"]
    return BillingRecord(
        policy_no=raw["policy_no"].strip(),
        line_code=raw["line_code"],
        bill_date=date(int(d[0:4]), int(d[4:6]), int(d[6:8])),
        premium_amt=zoned(raw["premium_amt"]),
        ipt_amt=zoned(raw["ipt_amt"]),
        currency=raw["currency"],
        region=raw["region"],
    )
'''

F[W + "corvane_loader/billing.py"] = '''"""Loads CORV.PRM.BILLING.DAILY (from JCL PRMNIGHT) into the warehouse.

Lineage (journey J3): PRMBILL -> CORV.PRM.BILLING.DAILY -> SFTP /landing/billing -> load_billing_file
-> dw.premium_billing_stage -> dw.fn_merge_billing() -> dw.premium_billing -> dw.v_premium_by_line
"""
import argparse
import configparser
import logging
import os
import pathlib
import shutil

from .billrec import RECORD_LENGTH, parse

log = logging.getLogger("corvane_loader.billing")

INSERT_STAGE = """INSERT INTO dw.premium_billing_stage
 (load_id, policy_no, line_code, bill_date, premium_amt, ipt_amt, currency, region)
 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""


def read_config(path: str = "loader.ini") -> configparser.ConfigParser:
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(path)
    return cfg


def load_billing_file(path: str, dsn: str, dry_run: bool = False) -> int:
    """Parse every 64-byte record, stage it, then merge into dw.premium_billing. Returns rows loaded."""
    records = []
    with open(path, encoding="ascii") as fh:
        for n, line in enumerate(fh, start=1):
            if len(line.rstrip("\\r\\n")) not in (RECORD_LENGTH, RECORD_LENGTH - 16):
                raise ValueError(f"{path}:{n}: record length {len(line.rstrip())} is not {RECORD_LENGTH}")
            records.append(parse(line))
    log.info("parsed %d billing records from %s", len(records), path)
    if dry_run:
        return len(records)

    import psycopg
    with psycopg.connect(dsn) as conn:
        load_id = conn.execute(
            "INSERT INTO dw.billing_load (file_name, record_count, started_at) VALUES (%s, %s, now()) RETURNING load_id",
            (os.path.basename(path), len(records))).fetchone()[0]
        with conn.cursor() as cur:
            cur.executemany(INSERT_STAGE, [(load_id, r.policy_no, r.line_code, r.bill_date, r.premium_amt,
                                            r.ipt_amt, r.currency, r.region) for r in records])
        merged = conn.execute("SELECT dw.fn_merge_billing(%s)", (load_id,)).fetchone()[0]
        conn.execute("UPDATE dw.billing_load SET merged_count = %s, finished_at = now() WHERE load_id = %s",
                     (merged, load_id))
    return len(records)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--file")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    cfg = read_config()
    landing = pathlib.Path(cfg["landing"]["billing_dir"])
    files = [pathlib.Path(args.file)] if args.file else sorted(landing.glob(cfg["landing"]["file_pattern"]))
    for f in files:
        load_billing_file(str(f), cfg["warehouse"]["dsn"], dry_run=args.dry_run)
        if not args.dry_run:
            shutil.move(str(f), cfg["landing"]["archive_dir"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
'''

F[W + "corvane_loader/closed_claims.py"] = '''"""Consumes claims.closed.v1 and appends to dw.claim_closed_fact for loss-ratio reporting."""
import json
import logging

log = logging.getLogger("corvane_loader.closed_claims")

UPSERT = """INSERT INTO dw.claim_closed_fact (claim_id, policy_number, line_code, closed_on, paid_amount, reserve_released, currency)
VALUES (%(claimId)s, %(policyNumber)s, %(lineCode)s, %(closedOn)s, %(paidAmount)s, %(reserveReleased)s, %(currency)s)
ON CONFLICT (claim_id) DO UPDATE SET paid_amount = EXCLUDED.paid_amount, closed_on = EXCLUDED.closed_on"""


def run(cfg) -> None:
    from confluent_kafka import Consumer
    import psycopg
    c = Consumer({"bootstrap.servers": cfg["kafka"]["bootstrap"], "group.id": cfg["kafka"]["group"],
                  "enable.auto.commit": False})
    c.subscribe([cfg["kafka"]["closed_topic"]])
    with psycopg.connect(cfg["warehouse"]["dsn"]) as conn:
        while True:
            msg = c.poll(1.0)
            if msg is None or msg.error():
                continue
            conn.execute(UPSERT, json.loads(msg.value()))
            conn.commit()
            c.commit(msg)
'''

F[W + "dags/premium_billing_load.py"] = '''"""Airflow DAG: loads the nightly premium billing file produced by mainframe JCL PRMNIGHT.

PRMNIGHT runs 01:30 Europe/London Mon-Sat and its STEP040 drops the file in /landing/billing.
This DAG starts at 04:00 and waits up to 2 hours for the file before failing (alert: BillingFileLate).
"""
from datetime import datetime, timedelta

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.sensors.filesystem import FileSensor

LONDON = pendulum.timezone("Europe/London")

with DAG(
    dag_id="premium_billing_load",
    schedule="0 4 * * 1-6",
    start_date=datetime(2026, 1, 5, tzinfo=LONDON),
    catchup=False,
    default_args={"owner": "team-data-platform", "retries": 2, "retry_delay": timedelta(minutes=10)},
    tags=["billing", "mainframe", "J3"],
) as dag:
    wait_for_file = FileSensor(
        task_id="wait_for_billing_file",
        filepath="/landing/billing/CORV.PRM.BILLING.DAILY.D{{ ds_nodash }}.txt",
        poke_interval=300,
        timeout=7200,
        mode="reschedule",
    )
    load = BashOperator(
        task_id="load_billing_file",
        bash_command="python -m corvane_loader.billing --file /landing/billing/CORV.PRM.BILLING.DAILY.D{{ ds_nodash }}.txt",
    )
    refresh_view = BashOperator(
        task_id="refresh_premium_by_line",
        bash_command="psql \\"$WAREHOUSE_DSN\\" -c 'REFRESH MATERIALIZED VIEW CONCURRENTLY dw.mv_premium_by_line_month'",
    )
    wait_for_file >> load >> refresh_view
'''

F[W + "tests/test_billrec.py"] = '''from datetime import date
from decimal import Decimal

from corvane_loader.billrec import parse, zoned

REC = "MTR000123456MTR20261102" + "00000045120" + "00000541{" + "GBPUK" + " " * 16


def test_record_is_64_bytes():
    assert len(REC) == 64


def test_parse_fields():
    r = parse(REC)
    assert r.policy_no == "MTR000123456"
    assert r.line_code == "MTR"
    assert r.bill_date == date(2026, 11, 2)
    assert r.premium_amt == Decimal("451.20")
    assert r.ipt_amt == Decimal("54.10")
    assert r.currency == "GBP" and r.region == "UK"


def test_negative_overpunch_is_a_refund():
    assert zoned("0000001234}") == Decimal("-123.40")
'''

nb = {
    "cells": [
        {"cell_type": "markdown", "metadata": {},
         "source": ["# Billing reconciliation (Nov 2026)\n",
                    "Compares the mainframe billing file with `dw.premium_billing` by product line.\n",
                    "Ad-hoc analysis by Data Platform; not scheduled."]},
        {"cell_type": "code", "execution_count": 1, "metadata": {},
         "source": ["import pandas as pd\n",
                    "stage = pd.read_sql('SELECT * FROM dw.premium_billing_stage WHERE load_id = 4182', conn)\n",
                    "dw = pd.read_sql('SELECT * FROM dw.v_premium_by_line', conn)\n",
                    "stage.merge(policyholders, on='policy_no').head(3)"],
         "outputs": [{"output_type": "execute_result", "execution_count": 1, "metadata": {},
                      "data": {"text/plain": [
                          "      policy_no line_code   premium_amt  holder_name        date_of_birth  postcode\n",
                          "0  MTR000123456       MTR        451.20  Alys Penhallow     1984-03-17     ZZ1 4QT\n",
                          "1  HOM000998877       HOM        612.75  Tomasz Wiercinski  1979-11-02     ZZ9 7LP\n",
                          "2  PET000441122       PET        188.40  Imogen Treharne    1992-06-28     ZZ3 2RD"]}}]},
        {"cell_type": "code", "execution_count": 2, "metadata": {},
         "source": ["diff = stage.groupby('line_code').premium_amt.sum() - dw.set_index('line_code').total_premium\n",
                    "diff[diff.abs() > 0.01]"],
         "outputs": [{"output_type": "execute_result", "execution_count": 2, "metadata": {},
                      "data": {"text/plain": ["line_code\n", "GDG    -14.20\n", "Name: premium_amt, dtype: float64"]}}]},
        {"cell_type": "markdown", "metadata": {},
         "source": ["GDG differs by -14.20: one refund record (negative overpunch `}`) was dropped by the old loader. "
                    "Fixed in loader 0.14.0."]},
    ],
    "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}},
    "nbformat": 4, "nbformat_minor": 5,
}
F[W + "notebooks/billing_reconciliation.ipynb"] = json.dumps(nb, indent=1) + "\n"

F["scripts/oneoff/backfill_2023_reserves.py"] = '''"""ONE-OFF (run once on 2024-01-14 by claims-platform, ticket CLM-2210). Do not schedule.

Backfills claims.claim_reserve for 2023 claims migrated from claims-v1, which stored reserves in a
free-text column. Uses the 2023 reserve factors, NOT the current ones in claims-service.
"""
import re
import sys

import psycopg

FACTORS_2023 = {"MTR": 1.10, "HOM": 1.25, "TRV": 1.00, "PET": 1.05}
AMOUNT = re.compile(r"(\\d+(?:\\.\\d{1,2})?)")


def main(dsn: str) -> None:
    with psycopg.connect(dsn) as conn:
        rows = conn.execute("""SELECT claim_id, line_code, legacy_reserve_text FROM claims.claim
                               WHERE EXTRACT(YEAR FROM reported_at) = 2023 AND legacy_reserve_text IS NOT NULL""").fetchall()
        for claim_id, line, text in rows:
            m = AMOUNT.search(text or "")
            if not m:
                continue
            amount = round(float(m.group(1)) * FACTORS_2023.get(line, 1.0), 2)
            conn.execute("""INSERT INTO claims.claim_reserve (claim_id, reserve_type, amount, currency, set_by, set_at)
                            VALUES (%s, 'INDEMNITY', %s, 'GBP', 'backfill-2023', now())
                            ON CONFLICT DO NOTHING""", (claim_id, amount))
        print(f"backfilled {len(rows)} reserves")


if __name__ == "__main__":
    main(sys.argv[1])
'''

F["scripts/oneoff/resend_policy_welcome_2025_06.sh"] = '''#!/usr/bin/env bash
# ONE-OFF (2025-06-12): replays policies.bound.v1 for 312 policies whose welcome email bounced during the
# SMTP relay outage (INC-0611). Kept for the incident record; never run again.
set -euo pipefail
: "${KAFKA_BOOTSTRAP:?}"
while read -r policy; do
  kcat -b "$KAFKA_BOOTSTRAP" -t policies.bound.v1 -P -k "$policy" <<< "$(psql "$POLICY_DSN" -Atc \\
    "select row_to_json(p) from policy.v_bound_event p where policy_number = '$policy'")"
done < "${1:-bounced_policies.txt}"
'''

for path, text in F.items():
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
print(f"wrote {len(F)} files")
