namespace Corvane.Commissions.Calculation;

public sealed class CommissionOptions
{
    public Dictionary<string, decimal> Rates { get; set; } = new();
    public VolumeBonusOptions VolumeBonus { get; set; } = new();
    public int ClawbackDays { get; set; } = 60;
    public int StatementDay { get; set; } = 3;
}

public sealed class VolumeBonusOptions
{
    public decimal ThresholdGbp { get; set; }
    public decimal ExtraRate { get; set; }
}
