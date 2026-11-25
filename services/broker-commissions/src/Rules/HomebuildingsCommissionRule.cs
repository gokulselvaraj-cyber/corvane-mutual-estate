using Corvane.Commissions.Calculation;

namespace Corvane.Commissions.Rules;

/// <summary>Home buildings (HOM): adjusts the base rate for multivehicle business, capped at 0.18.</summary>
public sealed class HomebuildingsCommissionRule : ILineCommissionRule
{
    public string LineCode => "HOM";

    public decimal AdjustRate(decimal baseRate, BoundPolicy policy)
    {
        var rate = baseRate;
        if (policy.Attributes.TryGetValue("MultiVehicle", out var flag) && flag == "true")
            rate += -0.02m;
        return Math.Min(rate, 0.18m);
    }
}
