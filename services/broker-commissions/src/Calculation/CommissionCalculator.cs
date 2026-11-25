using Corvane.Commissions.Rules;
using Microsoft.Extensions.Options;

namespace Corvane.Commissions.Calculation;

/// <summary>Works out broker commission for one bound policy (journey J6).</summary>
public sealed class CommissionCalculator
{
    private readonly CommissionOptions _options;

    public CommissionCalculator(IOptions<CommissionOptions> options) => _options = options.Value;

    public CommissionLine Calculate(BoundPolicy policy, decimal brokerYearToDateGwp)
    {
        if (!_options.Rates.TryGetValue(policy.LineCode, out var rate))
            throw new InvalidOperationException($"No commission rate for line {policy.LineCode}");

        // Commission is on net premium: insurance premium tax is never commissionable.
        var net = policy.GrossPremium - policy.IptAmount;
        var lineRule = LineCommissionRules.For(policy.LineCode);
        var adjustedRate = lineRule.AdjustRate(rate, policy);

        if (brokerYearToDateGwp >= _options.VolumeBonus.ThresholdGbp)
            adjustedRate += _options.VolumeBonus.ExtraRate;

        var amount = Math.Round(net * adjustedRate, 2, MidpointRounding.ToEven);
        return new CommissionLine(policy.PolicyNumber, policy.BrokerCode, policy.LineCode, net, adjustedRate,
                                  amount, policy.BoundAt.AddDays(_options.ClawbackDays));
    }
}

/// <summary>policies.bound.v1 as published by policy-admin; GrossPremium is the event's annualPremium.</summary>
public sealed record BoundPolicy(string PolicyNumber, string BrokerCode, string LineCode,
                                 [property: System.Text.Json.Serialization.JsonPropertyName("annualPremium")] decimal GrossPremium,
                                 decimal IptAmount, string Currency, DateTime BoundAt, IReadOnlyDictionary<string, string>? Attributes = null);

public sealed record CommissionLine(string PolicyNumber, string BrokerCode, string LineCode, decimal NetPremium,
                                    decimal Rate, decimal Amount, DateTime ClawbackUntil);
