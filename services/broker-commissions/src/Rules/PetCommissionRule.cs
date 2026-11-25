using Corvane.Commissions.Calculation;

namespace Corvane.Commissions.Rules;

/// <summary>Pet (PET): adjusts the base rate for highvalue business, capped at 0.25.</summary>
public sealed class PetCommissionRule : ILineCommissionRule
{
    public string LineCode => "PET";

    public decimal AdjustRate(decimal baseRate, BoundPolicy policy)
    {
        var rate = baseRate;
        if (policy.Attributes.TryGetValue("HighValue", out var flag) && flag == "true")
            rate += 0.01m;
        return Math.Min(rate, 0.25m);
    }
}
