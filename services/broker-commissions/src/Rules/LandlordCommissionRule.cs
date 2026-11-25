using Corvane.Commissions.Calculation;

namespace Corvane.Commissions.Rules;

/// <summary>Landlord (LLD): adjusts the base rate for multivehicle business, capped at 0.30.</summary>
public sealed class LandlordCommissionRule : ILineCommissionRule
{
    public string LineCode => "LLD";

    public decimal AdjustRate(decimal baseRate, BoundPolicy policy)
    {
        var rate = baseRate;
        if (policy.Attributes.TryGetValue("MultiVehicle", out var flag) && flag == "true")
            rate += -0.02m;
        return Math.Min(rate, 0.30m);
    }
}
