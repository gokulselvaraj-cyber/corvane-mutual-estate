using System.Text.Json;
using Confluent.Kafka;
using Corvane.Commissions.Calculation;
using Corvane.Commissions.Data;

namespace Corvane.Commissions.Consumers;

/// <summary>Reads policies.bound.v1 (published by policy-admin PolicyService.bind).</summary>
public sealed class BoundPolicyConsumer : BackgroundService
{
    private readonly IConfiguration _config;
    private readonly CommissionCalculator _calculator;
    private readonly StatementRepository _repo;
    private readonly ILogger<BoundPolicyConsumer> _log;

    public BoundPolicyConsumer(IConfiguration config, CommissionCalculator calculator, StatementRepository repo,
                               ILogger<BoundPolicyConsumer> log)
    {
        _config = config; _calculator = calculator; _repo = repo; _log = log;
    }

    protected override Task ExecuteAsync(CancellationToken stoppingToken) => Task.Run(() =>
    {
        var cfg = new ConsumerConfig
        {
            BootstrapServers = _config["Kafka:BootstrapServers"],
            GroupId = _config["Kafka:GroupId"],
            EnableAutoCommit = false,
            AutoOffsetReset = AutoOffsetReset.Earliest,
        };
        using var consumer = new ConsumerBuilder<string, string>(cfg).Build();
        consumer.Subscribe(_config["Kafka:Topic"]);
        while (!stoppingToken.IsCancellationRequested)
        {
            var result = consumer.Consume(stoppingToken);
            var evt = JsonSerializer.Deserialize<BoundPolicy>(result.Message.Value,
                new JsonSerializerOptions { PropertyNameCaseInsensitive = true })!;
            if (string.IsNullOrEmpty(evt.BrokerCode))
            {
                consumer.Commit(result); // direct business: no commission
                continue;
            }
            var ytd = _repo.BrokerYearToDateGwp(evt.BrokerCode, evt.BoundAt.Year);
            var line = _calculator.Calculate(evt, ytd);
            _repo.Insert(line, evt.BoundAt);
            _log.LogInformation("Commission {Amount} for {Policy} broker {Broker}", line.Amount, line.PolicyNumber, line.BrokerCode);
            consumer.Commit(result);
        }
    }, stoppingToken);
}
