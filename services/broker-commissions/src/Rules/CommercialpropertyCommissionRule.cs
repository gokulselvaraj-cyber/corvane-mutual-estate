using Corvane.Commissions.Calculation;

namespace Corvane.Commissions.Rules;

/// <summary>Commercial property (CPR): adjusts the base rate for bundle business, capped at 0.15.</summary>
public sealed class CommercialpropertyCommissionRule : ILineCommissionRule
{
    public string LineCode => "CPR";

    public decimal AdjustRate(decimal baseRate, BoundPolicy policy)
    {
        var rate = baseRate;
        if (policy.Attributes.TryGetValue("Bundle", out var flag) && flag == "true")
            rate += 0.01m;
        return Math.Min(rate, 0.15m);
    }
}
