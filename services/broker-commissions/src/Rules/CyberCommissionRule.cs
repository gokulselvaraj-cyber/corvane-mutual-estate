using Corvane.Commissions.Calculation;

namespace Corvane.Commissions.Rules;

/// <summary>Cyber (CYB): adjusts the base rate for renewal business, capped at 0.15.</summary>
public sealed class CyberCommissionRule : ILineCommissionRule
{
    public string LineCode => "CYB";

    public decimal AdjustRate(decimal baseRate, BoundPolicy policy)
    {
        var rate = baseRate;
        if (policy.Attributes.TryGetValue("Renewal", out var flag) && flag == "true")
            rate += 0.02m;
        return Math.Min(rate, 0.15m);
    }
}
