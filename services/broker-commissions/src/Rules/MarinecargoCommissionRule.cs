using Corvane.Commissions.Calculation;

namespace Corvane.Commissions.Rules;

/// <summary>Marine cargo (MAR): adjusts the base rate for online business, capped at 0.18.</summary>
public sealed class MarinecargoCommissionRule : ILineCommissionRule
{
    public string LineCode => "MAR";

    public decimal AdjustRate(decimal baseRate, BoundPolicy policy)
    {
        var rate = baseRate;
        if (policy.Attributes.TryGetValue("Online", out var flag) && flag == "true")
            rate += 0.015m;
        return Math.Min(rate, 0.18m);
    }
}
