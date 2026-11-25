"""Builder B bulk: one claim-rules class per product line in claims-service. Seeded, deterministic.
Run: python3 -I claims_gen.py <estate_root>"""
import os
import random
import sys

ROOT = sys.argv[1]
BASE = "services/claims-service/src/main/java/com/corvane/claims/lines"
rnd = random.Random(20261116)

LINES = {
    "MTR": ("Motor", ["REAR_END_COLLISION", "THEFT_OF_VEHICLE", "WINDSCREEN", "FIRE", "VANDALISM", "FLOOD_DAMAGE", "HIT_AND_RUN"]),
    "HOM": ("HomeBuildings", ["ESCAPE_OF_WATER", "STORM", "SUBSIDENCE", "FIRE", "FLOOD", "IMPACT", "MALICIOUS_DAMAGE"]),
    "CNT": ("HomeContents", ["THEFT", "ACCIDENTAL_DAMAGE", "ESCAPE_OF_WATER", "FIRE", "FREEZER_FAILURE", "LOST_JEWELLERY"]),
    "TRV": ("Travel", ["MEDICAL_ABROAD", "CANCELLATION", "LOST_BAGGAGE", "DELAYED_DEPARTURE", "PERSONAL_LIABILITY"]),
    "PET": ("Pet", ["ILLNESS", "ACCIDENTAL_INJURY", "DENTAL", "THIRD_PARTY_LIABILITY", "STRAYING_ADVERTISING"]),
    "LLD": ("Landlord", ["RENT_ARREARS", "TENANT_DAMAGE", "ESCAPE_OF_WATER", "LOSS_OF_RENT", "STORM"]),
    "MAR": ("MarineCargo", ["GENERAL_AVERAGE", "JETTISON", "CONTAINER_LOSS", "WATER_INGRESS", "PILFERAGE"]),
    "CPR": ("CommercialProperty", ["FIRE", "BUSINESS_INTERRUPTION", "MACHINERY_BREAKDOWN", "THEFT", "FLOOD"]),
    "PLB": ("PublicLiability", ["SLIP_TRIP_FALL", "PROPERTY_DAMAGE_THIRD_PARTY", "PRODUCT_INJURY", "FOOD_POISONING"]),
    "PIN": ("ProfessionalIndemnity", ["NEGLIGENT_ADVICE", "BREACH_OF_DUTY", "LOSS_OF_DOCUMENTS", "DEFAMATION"]),
    "CYB": ("Cyber", ["RANSOMWARE", "DATA_BREACH", "BUSINESS_EMAIL_COMPROMISE", "DDOS_OUTAGE", "SOCIAL_ENGINEERING"]),
    "GDG": ("Gadget", ["ACCIDENTAL_DAMAGE", "THEFT", "LIQUID_DAMAGE", "MECHANICAL_BREAKDOWN", "LOSS"]),
}

TEMPLATE = """package com.corvane.claims.lines.{pkg};

import com.corvane.claims.api.ClaimDtos.FnolRequest;
import com.corvane.claims.domain.Reserve;
import com.corvane.claims.lines.LineRules;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.Map;
import java.util.Set;

/**
 * {title} ({code}) claim rules: accepted loss causes, reporting window and the initial reserve.
 * Generated from the claims rule book {book}; edit the rule book, not this file.
 */
public final class {cls}ClaimRules {{
    private {cls}ClaimRules() {{}}

    /** Loss cause -> initial reserve factor applied to the claimant's estimate. */
    static final Map<String, BigDecimal> RESERVE_FACTORS = Map.ofEntries(
{factors}
    );

    /** Causes always referred to a specialist, whatever the amount. */
    static final Set<String> ALWAYS_REFER = Set.of({refer});

    /** Loss cause -> documents the claimant must supply before settlement. */
    static final Map<String, String> REQUIRED_DOCUMENTS = Map.ofEntries(
{docs}
    );

    /** Loss cause -> handling note shown to the adjuster (claims manual {book}). */
    static final Map<String, String> HANDLING_NOTES = Map.ofEntries(
{notes}
    );

    static final int REPORTING_WINDOW_DAYS = {window};
    static final BigDecimal MAX_SINGLE_CLAIM = new BigDecimal("{maxclaim}");
    static final BigDecimal EXPENSE_LOADING = new BigDecimal("{expense}");

    @Component
    public static class Validator implements LineRules.LineValidator {{
        @Override public String lineCode() {{ return "{code}"; }}

        @Override
        public void validate(FnolRequest request) {{
            if (!RESERVE_FACTORS.containsKey(request.lossCause())) {{
                throw new IllegalArgumentException("{code}: unknown loss cause " + request.lossCause());
            }}
            long late = ChronoUnit.DAYS.between(request.incidentDate(), LocalDate.now());
            if (late > REPORTING_WINDOW_DAYS) {{
                throw new IllegalArgumentException("{code}: reported " + late + " days after the incident, window is "
                        + REPORTING_WINDOW_DAYS);
            }}
            if (request.estimatedAmount().compareTo(MAX_SINGLE_CLAIM) > 0) {{
                throw new IllegalArgumentException("{code}: estimate above the single-claim limit " + MAX_SINGLE_CLAIM);
            }}
{extra}
        }}
    }}

    @Component
    public static class ReserveCalculator implements LineRules.LineReserveCalculator {{
        @Override public String lineCode() {{ return "{code}"; }}

        @Override
        public Reserve initialReserve(FnolRequest request) {{
            BigDecimal factor = RESERVE_FACTORS.getOrDefault(request.lossCause(), BigDecimal.ONE);
            BigDecimal indemnity = request.estimatedAmount().multiply(factor).setScale(2, RoundingMode.HALF_UP);
            BigDecimal floor = new BigDecimal("{floor}");
            if (indemnity.compareTo(floor) < 0) {{
                indemnity = floor;
            }}
            if (ALWAYS_REFER.contains(request.lossCause())) {{
                indemnity = indemnity.multiply(new BigDecimal("{referload}")).setScale(2, RoundingMode.HALF_UP);
            }}
            BigDecimal expenses = indemnity.multiply(EXPENSE_LOADING).setScale(2, RoundingMode.HALF_UP);
            return new Reserve("{code}", indemnity, expenses);
        }}
    }}
}}
"""

EXTRAS = {
    "MTR": '            if (request.incidentPostcode() == null) {\n                throw new IllegalArgumentException("MTR: incident postcode is required for motor claims");\n            }',
    "TRV": '            if ("MEDICAL_ABROAD".equals(request.lossCause()) && (request.injuryNotes() == null || request.injuryNotes().isBlank())) {\n                throw new IllegalArgumentException("TRV: medical claims need treatment notes");\n            }',
    "PET": '            if ("DENTAL".equals(request.lossCause()) && request.estimatedAmount().compareTo(new BigDecimal("1500")) > 0) {\n                throw new IllegalArgumentException("PET: dental capped at 1,500 per condition");\n            }',
    "CYB": '            if (request.description() == null || request.description().length() < 200) {\n                throw new IllegalArgumentException("CYB: incident narrative of at least 200 characters required");\n            }',
    "GDG": '            if ("LOSS".equals(request.lossCause())) {\n                throw new IllegalArgumentException("GDG: loss is covered only on Gadget Plus; route to manual check");\n            }',
}

DOCS = ["photos of the damage", "repair estimate from an approved repairer", "police crime reference",
        "proof of purchase or valuation", "invoice for emergency repairs", "medical report", "vet invoice",
        "carrier's bill of lading", "tenancy agreement", "forensic IT report", "witness statements",
        "bank statements for the period", "booking confirmation", "letter of complaint from the third party",
        "loss adjuster's site report", "drainage survey", "weather station report for the date"]
ACTIONS = ["Appoint a loss adjuster when the estimate exceeds {n} GBP.", "Check for a prior claim on the same item within {n} days.",
           "Offer a cash settlement up to {n} GBP if the claimant agrees.", "Instruct a specialist within {n} hours of notification.",
           "Request the documents again after {n} days, then close as withdrawn.", "Escalate to the claims manager above {n} GBP.",
           "Do not pay before the {n}-day cooling-off for disputed liability.", "Use the approved supplier panel; out-of-panel repairs capped at {n} GBP.",
           "Ask the fraud team to review if the policy is under {n} days old.", "Arrange an inspection within {n} working days."]

count = 0
for code, (title, causes) in LINES.items():
    factors = []
    for c in causes:
        factors.append(f'            Map.entry("{c}", new BigDecimal("{rnd.uniform(0.6, 1.6):.2f}"))')
    refer = ", ".join(f'"{c}"' for c in rnd.sample(causes, k=rnd.randint(1, 2)))
    docs = []
    notes = []
    for c in causes:
        d = "; ".join(rnd.sample(DOCS, k=rnd.randint(2, 4)))
        docs.append(f'            Map.entry("{c}", "{d}")')
        a = " ".join(x.format(n=rnd.choice([3, 5, 7, 10, 14, 21, 30, 60, 90, 250, 500, 1000, 2500, 7500, 15000]))
                     for x in rnd.sample(ACTIONS, k=rnd.randint(2, 3)))
        notes.append(f'            Map.entry("{c}", "{a}")')
    body = TEMPLATE.format(docs=",\n".join(docs), notes=",\n".join(notes),
        pkg=code.lower(), code=code, title=title, cls=title, book=f"CRB-{code}-{rnd.randint(3, 9)}.{rnd.randint(0, 4)}",
        factors=",\n".join(factors), refer=refer, window=rnd.choice([14, 30, 31, 60, 90, 180]),
        maxclaim=rnd.choice(["5000", "25000", "75000", "250000", "1000000", "2500"]),
        expense=f"{rnd.uniform(0.03, 0.18):.2f}", floor=rnd.choice(["50", "100", "250", "500", "1000"]),
        referload=f"{rnd.uniform(1.1, 1.5):.2f}", extra=EXTRAS.get(code, "            // no line-specific checks"))
    path = os.path.join(ROOT, BASE, code.lower(), f"{title}ClaimRules.java")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    count += 1
print(f"claims_gen: wrote {count} files")
