"""Builder C bulk: per-product-line fraud rules, notification templates and C# commission rules.

Seeded and deterministic. Run: python3 -I services_gen.py <estate_root>
"""
import os
import random
import sys

ROOT = sys.argv[1]
rng = random.Random(20261116)

LINES = {
    "MTR": ("Motor", ["COLLISION_THIRD_PARTY", "COLLISION_SINGLE", "THEFT_VEHICLE", "WINDSCREEN", "VANDALISM", "FIRE_VEHICLE"],
            ["vehicle_age_years", "annual_mileage", "garaged", "dashcam_footage", "third_party_count"],
            "whiplash claimed after a low-speed impact"),
    "HOM": ("Home buildings", ["ESCAPE_OF_WATER", "STORM", "FLOOD", "SUBSIDENCE", "FIRE", "IMPACT"],
            ["property_age_years", "unoccupied_days", "roof_type", "trace_and_access", "contractor_quote_only"],
            "damage reported after a long unoccupied period"),
    "CNT": ("Home contents", ["THEFT_BURGLARY", "ACCIDENTAL_DAMAGE", "ESCAPE_OF_WATER", "FIRE", "LOSS_AWAY"],
            ["items_claimed", "receipts_provided", "forced_entry", "police_reference", "single_item_max"],
            "high-value items with no receipts and no forced entry"),
    "TRV": ("Travel", ["MEDICAL_ABROAD", "CANCELLATION", "BAGGAGE_LOSS", "DELAY", "PERSONAL_MONEY"],
            ["days_abroad", "destination_risk", "booking_to_departure_days", "medical_provider_known", "police_report"],
            "trip cancelled shortly after the policy was bought"),
    "PET": ("Pet", ["ILLNESS", "ACCIDENT", "DENTAL", "THIRD_PARTY", "DEATH"],
            ["pet_age_years", "breed_risk", "vet_visits_12m", "pre_existing_flag", "vet_practice_changed"],
            "condition first noted before the policy start"),
    "LLD": ("Landlord", ["MALICIOUS_DAMAGE_TENANT", "LOSS_OF_RENT", "ESCAPE_OF_WATER", "STORM", "FIRE"],
            ["tenancy_months", "tenant_type", "void_days", "agent_managed", "inventory_check"],
            "loss of rent claimed with no tenancy agreement"),
    "MAR": ("Marine cargo", ["GENERAL_AVERAGE", "THEFT_IN_TRANSIT", "WATER_INGRESS", "HANDLING_DAMAGE", "TOTAL_LOSS"],
            ["voyage_days", "transhipments", "container_sealed", "cargo_value_band", "survey_report"],
            "seal numbers do not match the bill of lading"),
    "CPR": ("Commercial property", ["FIRE", "BUSINESS_INTERRUPTION", "THEFT_COMMERCIAL", "FLOOD", "MACHINERY_BREAKDOWN"],
            ["trading_years", "sprinklers", "alarm_grade", "turnover_drop_pct", "accounts_late"],
            "fire shortly after turnover fell sharply"),
    "PLB": ("Public liability", ["SLIP_TRIP", "PROPERTY_DAMAGE_TP", "PRODUCT_INJURY", "FOOD_POISONING"],
            ["witnesses", "cctv_available", "claimant_solicitor_first", "days_to_notify", "injury_severity"],
            "claimant represented before the incident was reported to us"),
    "PIN": ("Professional indemnity", ["NEGLIGENCE", "BREACH_OF_DUTY", "LOSS_OF_DOCUMENTS", "DEFAMATION"],
            ["profession", "years_qualified", "fee_dispute", "retroactive_date_gap", "prior_notifications"],
            "claim follows a fee dispute with the same client"),
    "CYB": ("Cyber", ["RANSOMWARE", "DATA_BREACH", "BUSINESS_EMAIL_COMPROMISE", "DDOS", "SYSTEM_FAILURE"],
            ["mfa_enabled", "backup_tested", "records_affected", "ransom_paid", "patch_age_days"],
            "MFA declared at inception but absent at the time of loss"),
    "GDG": ("Gadget", ["ACCIDENTAL_DAMAGE", "THEFT_DEVICE", "LIQUID_DAMAGE", "BREAKDOWN", "LOSS"],
            ["device_age_months", "imei_blocked", "proof_of_purchase", "claims_on_device", "bought_second_hand"],
            "device claimed lost within weeks of a policy upgrade"),
}


def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


count = 0
test_rows = []
for code, (name, causes, attrs, scenario) in LINES.items():
    # ---------- fraud rule module ----------
    hot_causes = rng.sample(causes, k=2)
    cause_w = round(rng.uniform(0.08, 0.2), 2)
    amount_cap = rng.choice([1500, 2500, 4000, 7500, 12000, 25000, 60000])
    amount_w = round(rng.uniform(0.1, 0.25), 2)
    a1, a2, a3 = rng.sample(attrs, k=3)
    t1 = rng.choice([2, 3, 5, 10, 30, 90])
    w1, w2, w3 = (round(rng.uniform(0.05, 0.3), 2) for _ in range(3))
    window = rng.choice([7, 14, 21, 45, 60])
    window_w = round(rng.uniform(0.1, 0.3), 2)
    write(f"services/fraud-scoring/corvane_fraud/rules/line_{code.lower()}.py", f'''"""{name} ({code}) fraud indicators.

Typical pattern the counter-fraud team asked us to catch: {scenario}.
Weights reviewed by Fraud Analytics; generated from the rules catalogue (fraud-rules-2026.02).
"""
from ..models import Indicator, ScoreRequest

LINE = "{code}"
HIGH_RISK_CAUSES = {tuple(sorted(hot_causes))!r}
LARGE_LOSS_GBP = {amount_cap}
EARLY_WINDOW_DAYS = {window}


def evaluate(req: ScoreRequest) -> list[Indicator]:
    out: list[Indicator] = []
    attrs = req.attributes or {{}}
    if req.loss_cause in HIGH_RISK_CAUSES:
        out.append(Indicator(code="{code}_CAUSE", weight={cause_w}, detail=f"high-risk cause {{req.loss_cause}}"))
    if req.claimed_amount > LARGE_LOSS_GBP:
        out.append(Indicator(code="{code}_LARGE_LOSS", weight={amount_w}, detail="above {amount_cap} GBP"))
    if (req.loss_date - req.policy_start_date).days < EARLY_WINDOW_DAYS:
        out.append(Indicator(code="{code}_EARLY", weight={window_w}, detail="{scenario}"))
    if attrs.get("{a1}") in (True, "yes") or (isinstance(attrs.get("{a1}"), (int, float)) and attrs["{a1}"] >= {t1}):
        out.append(Indicator(code="{code}_{a1.upper()}", weight={w1}, detail="{a1.replace('_', ' ')} at or above {t1}"))
    if attrs.get("{a2}") in (False, "no", 0):
        out.append(Indicator(code="{code}_NO_{a2.upper()}", weight={w2}, detail="{a2.replace('_', ' ')} missing"))
    if attrs.get("{a3}") == "unknown":
        out.append(Indicator(code="{code}_{a3.upper()}_UNKNOWN", weight={w3}, detail="{a3.replace('_', ' ')} not given"))
    return out
''')
    test_rows.append((code, sorted(hot_causes)[0], amount_cap))

    # ---------- notification template ----------
    tips = {
        "MTR": "Keep any dashcam footage and the other driver's details.",
        "HOM": "Make the property safe and keep damaged items until we have seen them.",
        "CNT": "Gather receipts, photos or bank statements for the items claimed.",
        "TRV": "Keep boarding passes, medical bills and the airline's delay letter.",
        "PET": "Ask your vet to complete the claim form in My Corvane.",
        "LLD": "Send us the tenancy agreement and the check-in inventory.",
        "MAR": "Do not dispose of damaged cargo until the surveyor has attended.",
        "CPR": "Keep trading records; a loss adjuster will contact you within 2 working days.",
        "PLB": "Do not admit liability; forward any letters from the claimant to us unanswered.",
        "PIN": "Do not contact the client about the claim; our panel solicitor will advise.",
        "CYB": "Do not pay any ransom; our incident response partner will call you within 1 hour.",
        "GDG": "If your device was stolen, block it with your network and get a police reference.",
    }[code]
    write(f"services/notifications/src/templates/claim-registered-{code.lower()}.hbs", f'''<p>Dear {{{{name}}}},</p>
<p>We have registered your {name.lower()} claim <strong>{{{{claimId}}}}</strong>.</p>
{{{{#if autoApproved}}}}
<p>Good news: your claim has been approved. Payment will reach your account within 3 working days.</p>
{{{{else}}}}
<p>A claims handler will contact you within {rng.choice([1, 2, 3])} working day(s).</p>
{{{{/if}}}}
<p>{tips}</p>
<p><a href="{{{{trackUrl}}}}">Track your claim</a></p>
<p>Corvane Mutual Claims</p>
''')

    # ---------- C# commission rule ----------
    cls = name.replace(" ", "")
    attr = rng.choice(["MultiVehicle", "NewBusiness", "Renewal", "Bundle", "HighValue", "Online"])
    delta = rng.choice(["-0.02m", "-0.01m", "0.01m", "0.015m", "0.02m"])
    cap = rng.choice(["0.15m", "0.18m", "0.20m", "0.25m", "0.30m"])
    write(f"services/broker-commissions/src/Rules/{cls}CommissionRule.cs", f'''using Corvane.Commissions.Calculation;

namespace Corvane.Commissions.Rules;

/// <summary>{name} ({code}): adjusts the base rate for {attr.lower()} business, capped at {cap.rstrip("m")}.</summary>
public sealed class {cls}CommissionRule : ILineCommissionRule
{{
    public string LineCode => "{code}";

    public decimal AdjustRate(decimal baseRate, BoundPolicy policy)
    {{
        var rate = baseRate;
        if (policy.Attributes.TryGetValue("{attr}", out var flag) && flag == "true")
            rate += {delta};
        return Math.Min(rate, {cap});
    }}
}}
''')
    count += 3

reg_lines = "\n".join(f'        ["{c}"] = new {n.replace(" ", "")}CommissionRule(),' for c, (n, *_rest) in LINES.items())
write("services/broker-commissions/src/Rules/LineCommissionRules.cs", f'''using Corvane.Commissions.Calculation;

namespace Corvane.Commissions.Rules;

public interface ILineCommissionRule
{{
    string LineCode {{ get; }}
    decimal AdjustRate(decimal baseRate, BoundPolicy policy);
}}

public static class LineCommissionRules
{{
    private static readonly Dictionary<string, ILineCommissionRule> Rules = new()
    {{
{reg_lines}
    }};

    public static ILineCommissionRule For(string lineCode) =>
        Rules.TryGetValue(lineCode, out var rule) ? rule : throw new InvalidOperationException($"No rule for {{lineCode}}");
}}
''')

rows = "\n".join(f'    ("{c}", "{cause}", {cap}),' for c, cause, cap in test_rows)
write("services/fraud-scoring/tests/test_line_rules.py", f'''"""One check per product line: a high-risk cause above the large-loss amount raises line indicators."""
from decimal import Decimal

import pytest

from corvane_fraud.rules import registry

CASES = [
{rows}
]


@pytest.mark.parametrize("line,cause,cap", CASES)
def test_line_indicators(make_request, line, cause, cap):
    req = make_request(line_code=line, loss_cause=cause, claimed_amount=Decimal(cap + 1))
    codes = {{i.code for i in registry.for_line(line).evaluate(req)}}
    assert f"{{line}}_CAUSE" in codes and f"{{line}}_LARGE_LOSS" in codes


def test_every_line_has_a_module():
    for line in registry.LINES:
        assert hasattr(registry.for_line(line), "evaluate")
''')
print(f"generated {count + 2} files")
