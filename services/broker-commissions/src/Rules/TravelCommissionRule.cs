using Corvane.Commissions.Calculation;

namespace Corvane.Commissions.Rules;

/// <summary>Travel (TRV): adjusts the base rate for newbusiness business, capped at 0.15.</summary>
public sealed class TravelCommissionRule : ILineCommissionRule
{
    public string LineCode => "TRV";

    public decimal AdjustRate(decimal baseRate, BoundPolicy policy)
    {
        var rate = baseRate;
        if (policy.Attributes.TryGetValue("NewBusiness", out var flag) && flag == "true")
            rate += -0.02m;
        return Math.Min(rate, 0.15m);
    }
}
