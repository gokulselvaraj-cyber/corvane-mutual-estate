using Corvane.Commissions.Calculation;
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
