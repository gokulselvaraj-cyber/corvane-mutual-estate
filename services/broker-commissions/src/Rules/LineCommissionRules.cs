using Corvane.Commissions.Calculation;

namespace Corvane.Commissions.Rules;

public interface ILineCommissionRule
{
    string LineCode { get; }
    decimal AdjustRate(decimal baseRate, BoundPolicy policy);
}

public static class LineCommissionRules
{
    private static readonly Dictionary<string, ILineCommissionRule> Rules = new()
    {
        ["MTR"] = new MotorCommissionRule(),
        ["HOM"] = new HomebuildingsCommissionRule(),
        ["CNT"] = new HomecontentsCommissionRule(),
        ["TRV"] = new TravelCommissionRule(),
        ["PET"] = new PetCommissionRule(),
        ["LLD"] = new LandlordCommissionRule(),
        ["MAR"] = new MarinecargoCommissionRule(),
        ["CPR"] = new CommercialpropertyCommissionRule(),
        ["PLB"] = new PublicliabilityCommissionRule(),
        ["PIN"] = new ProfessionalindemnityCommissionRule(),
        ["CYB"] = new CyberCommissionRule(),
        ["GDG"] = new GadgetCommissionRule(),
    };

    public static ILineCommissionRule For(string lineCode) =>
        Rules.TryGetValue(lineCode, out var rule) ? rule : throw new InvalidOperationException($"No rule for {lineCode}");
}
