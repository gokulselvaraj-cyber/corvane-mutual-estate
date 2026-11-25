using Corvane.Commissions.Calculation;

namespace Corvane.Commissions.Rules;

/// <summary>Motor (MTR): adjusts the base rate for highvalue business, capped at 0.30.</summary>
public sealed class MotorCommissionRule : ILineCommissionRule
{
    public string LineCode => "MTR";

    public decimal AdjustRate(decimal baseRate, BoundPolicy policy)
    {
        var rate = baseRate;
        if (policy.Attributes.TryGetValue("HighValue", out var flag) && flag == "true")
            rate += -0.01m;
        return Math.Min(rate, 0.30m);
    }
}
