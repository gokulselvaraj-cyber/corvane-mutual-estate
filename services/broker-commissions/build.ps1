# Local build and test for broker-commissions (Windows developer machines).
param([string]$Configuration = "Release")
$ErrorActionPreference = "Stop"
dotnet restore Corvane.Commissions.csproj
dotnet build Corvane.Commissions.csproj -c $Configuration --no-restore
dotnet test tests/Corvane.Commissions.Tests.csproj -c $Configuration
Write-Host "broker-commissions built ($Configuration)"
