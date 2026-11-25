using Corvane.Commissions.Calculation;

namespace Corvane.Commissions.Rules;

/// <summary>Professional indemnity (PIN): adjusts the base rate for renewal business, capped at 0.18.</summary>
public sealed class ProfessionalindemnityCommissionRule : ILineCommissionRule
{
    public string LineCode => "PIN";

    public decimal AdjustRate(decimal baseRate, BoundPolicy policy)
    {
        var rate = baseRate;
        if (policy.Attributes.TryGetValue("Renewal", out var flag) && flag == "true")
            rate += -0.01m;
        return Math.Min(rate, 0.18m);
    }
}
