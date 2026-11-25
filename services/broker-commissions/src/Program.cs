using Corvane.Commissions.Calculation;
using Corvane.Commissions.Consumers;
using Corvane.Commissions.Data;

var builder = Host.CreateApplicationBuilder(args);
builder.Services.Configure<CommissionOptions>(builder.Configuration.GetSection("Commission"));
builder.Services.AddSingleton<CommissionCalculator>();
builder.Services.AddSingleton<StatementRepository>();
builder.Services.AddHostedService<BoundPolicyConsumer>();
builder.Build().Run();
