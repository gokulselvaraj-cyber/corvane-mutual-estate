using Corvane.Commissions.Calculation;
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
