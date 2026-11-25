"""Builder A bulk: per-product-line rating rules + tests + Liquibase factor tables for policy-admin.
Seeded and deterministic. Run: python3 -I policyadmin_gen.py <estate_root>"""
import os
import random
import sys

ROOT = sys.argv[1]
PA = "services/policy-admin/"
J = PA + "src/main/java/com/corvane/policy/rating/"
T = PA + "src/test/java/com/corvane/policy/rating/"

# code, class prefix, label, per-1000 rate range, min premium, max sum insured, factors {name: [options]}, referral rules
LINES = [
    ("MTR", "Mtr", "Motor", (18, 32), 240, 120000,
     {"vehicleGroup": ["1-10", "11-20", "21-30", "31-40", "41-50"], "annualMileage": ["<5k", "5-10k", "10-15k", ">15k"],
      "overnight": ["garage", "driveway", "street"], "use": ["social", "commuting", "business"]},
     [("vehicleGroup", "41-50", "Vehicle group 41-50 needs underwriter review"), ("use", "business", None)]),
    ("HOM", "Hom", "Home buildings", (0.9, 1.6), 140, 2000000,
     {"buildYear": ["pre-1900", "1900-1945", "1946-1990", "post-1990"], "floodZone": ["1", "2", "3"],
      "roof": ["tile", "slate", "flat", "thatch"], "listed": ["no", "grade II", "grade I"]},
     [("floodZone", "3", "Flood zone 3"), ("roof", "thatch", "Thatched roof"), ("listed", "grade I", "Grade I listed")]),
    ("CNT", "Cnt", "Home contents", (3.5, 6.0), 60, 150000,
     {"locks": ["BS3621", "other"], "alarm": ["monitored", "bells-only", "none"], "occupancy": ["owner", "tenant", "student"]},
     [("occupancy", "student", None)]),
    ("TRV", "Trv", "Travel", (9, 15), 18, 10000000,
     {"region": ["UK", "Europe", "Worldwide-ex-USA", "Worldwide"], "tripType": ["single", "annual"],
      "winterSports": ["no", "yes"], "medicalConditions": ["none", "declared", "undeclared"]},
     [("medicalConditions", "declared", "Declared medical conditions need screening")]),
    ("PET", "Pet", "Pet", (28, 45), 72, 15000,
     {"species": ["dog", "cat", "rabbit"], "breedGroup": ["crossbreed", "pedigree", "dangerous-dogs-act"],
      "cover": ["accident", "time-limited", "lifetime"], "neutered": ["yes", "no"]},
     [("breedGroup", "dangerous-dogs-act", "Breed listed under the Dangerous Dogs Act")]),
    ("LLD", "Lld", "Landlord", (1.4, 2.4), 180, 3000000,
     {"tenantType": ["professional", "student", "DSS", "holiday-let"], "units": ["1", "2-4", "5+"],
      "unoccupiedDays": ["0-30", "31-60", "60+"]},
     [("unoccupiedDays", "60+", "Unoccupied over 60 days"), ("units", "5+", "HMO with 5+ units")]),
    ("MAR", "Mar", "Marine cargo", (0.6, 1.3), 450, 25000000,
     {"conveyance": ["container-ship", "bulk", "air", "road"], "commodity": ["general", "perishable", "hazardous", "fine-art"],
      "route": ["intra-EU", "transatlantic", "Asia-Europe", "high-risk-waters"]},
     [("route", "high-risk-waters", "Route through listed high-risk waters"), ("commodity", "fine-art", "Fine art cargo")]),
    ("CPR", "Cpr", "Commercial property", (1.8, 3.2), 600, 50000000,
     {"construction": ["standard", "composite-panel", "timber-frame"], "sprinklers": ["yes", "no"],
      "trade": ["office", "retail", "warehouse", "manufacturing", "food-processing"]},
     [("construction", "composite-panel", "Composite panel construction"), ("trade", "food-processing", None)]),
    ("PLB", "Plb", "Public liability", (2.2, 4.0), 120, 10000000,
     {"trade": ["consultant", "retail", "hospitality", "construction", "events"], "turnoverBand": ["<250k", "250k-1m", "1m-5m", ">5m"],
      "workAtHeight": ["no", "under-10m", "over-10m"]},
     [("workAtHeight", "over-10m", "Work at height above 10m")]),
    ("PIN", "Pin", "Professional indemnity", (4.5, 8.0), 300, 5000000,
     {"profession": ["IT-consultant", "architect", "accountant", "solicitor", "financial-adviser"],
      "feeIncomeBand": ["<100k", "100k-500k", "500k-2m", ">2m"], "usWork": ["none", "<10%", ">10%"]},
     [("usWork", ">10%", "More than 10% US work"), ("profession", "financial-adviser", "Regulated advice")]),
    ("CYB", "Cyb", "Cyber", (6, 11), 350, 5000000,
     {"mfa": ["all-users", "admins-only", "none"], "backups": ["offline-tested", "online-only", "none"],
      "recordsHeld": ["<10k", "10k-100k", ">100k"], "sector": ["professional", "retail", "healthcare", "education"]},
     [("mfa", "none", "No multi-factor authentication"), ("backups", "none", "No backups")]),
    ("GDG", "Gdg", "Gadget", (65, 110), 45, 6000,
     {"device": ["phone", "laptop", "tablet", "wearable", "console"], "age": ["new", "<1y", "1-2y", ">2y"],
      "theftCover": ["yes", "no"]},
     [("age", ">2y", None)]),
]

rng = random.Random(20261116)


def w(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


changesets = []
test_bodies = []
for code, cls, label, (lo, hi), minimum, max_si, factors, referrals in LINES:
    rate = round(rng.uniform(lo, hi), 3)
    prior_loading = round(rng.uniform(0.08, 0.30), 2)
    prior_refer = rng.choice([2, 3, 4])
    age_bands = sorted(rng.sample(range(21, 76), 3))
    age_load = [round(rng.uniform(1.05, 1.6), 2), 1.0, round(rng.uniform(0.85, 0.98), 2), round(rng.uniform(1.02, 1.35), 2)]
    area_load = {a: round(rng.uniform(0.85, 1.45), 2) for a in sorted(rng.sample(
        ["B", "BS", "CF", "E", "EH", "G", "L", "LS", "M", "N", "NE", "SE", "SW", "W"], 5))}
    fac_tables = {}
    for name, opts in factors.items():
        vals = [1.0] + [round(rng.uniform(0.8, 1.9), 2) for _ in opts[1:]]
        fac_tables[name] = list(zip(opts, vals))

    lines = []
    lines.append(f"package com.corvane.policy.rating;\n\n")
    lines.append("import com.corvane.policy.domain.ProductLine;\nimport com.corvane.policy.domain.RatingInput;\n"
                 "import org.springframework.stereotype.Component;\n\nimport java.math.BigDecimal;\n"
                 "import java.math.RoundingMode;\nimport java.util.Map;\nimport java.util.Optional;\n\n")
    lines.append(f"/**\n * {label} ({code}) rating rules: Java port of mainframe program RAT{code}01.\n"
                 f" * Base rate {rate} per 1,000 sum insured, minimum premium {minimum} GBP, maximum sum insured {max_si:,}.\n"
                 f" * Generated from the rating workbook RW-{code}-2026Q3; edit the workbook, not this file.\n */\n")
    lines.append(f"@Component\npublic class {cls}RatingRules implements LineRatingRules {{\n\n")
    lines.append(f"    static final BigDecimal RATE_PER_1000 = new BigDecimal(\"{rate}\");\n")
    lines.append(f"    static final BigDecimal MINIMUM_PREMIUM = new BigDecimal(\"{minimum}\");\n")
    lines.append(f"    static final BigDecimal MAX_SUM_INSURED = new BigDecimal(\"{max_si}\");\n")
    lines.append(f"    static final BigDecimal PRIOR_CLAIM_LOADING = new BigDecimal(\"{prior_loading}\");\n")
    lines.append(f"    static final int REFER_PRIOR_CLAIMS = {prior_refer};\n\n")
    for name, table in fac_tables.items():
        const = "".join("_" + c if c.isupper() else c.upper() for c in name)
        entries = ", ".join(f'"{o}", new BigDecimal("{v}")' for o, v in table)
        lines.append(f"    static final Map<String, BigDecimal> {const} = Map.of({entries});\n")
    area_entries = ", ".join(f'"{a}", new BigDecimal("{v}")' for a, v in area_load.items())
    lines.append(f"    static final Map<String, BigDecimal> AREA = Map.of({area_entries});\n\n")
    lines.append(f"    @Override\n    public ProductLine line() {{ return ProductLine.{code}; }}\n\n")
    lines.append("    @Override\n    public BigDecimal basePremium(RatingInput in) {\n")
    lines.append("        BigDecimal p = in.sumInsured().divide(BigDecimal.valueOf(1000)).multiply(RATE_PER_1000);\n")
    for name in fac_tables:
        const = "".join("_" + c if c.isupper() else c.upper() for c in name)
        default = fac_tables[name][0][0]
        lines.append(f"        p = p.multiply({const}.getOrDefault(in.factors().getOrDefault(\"{name}\", \"{default}\"), BigDecimal.ONE));\n")
    lines.append("        p = p.multiply(AREA.getOrDefault(area(in.postcode()), BigDecimal.ONE));\n")
    lines.append("        p = p.multiply(ageLoading(in.holderAge()));\n")
    lines.append("        p = p.multiply(BigDecimal.ONE.add(PRIOR_CLAIM_LOADING.multiply(BigDecimal.valueOf(in.priorClaims()))));\n")
    lines.append("        return p.max(MINIMUM_PREMIUM).setScale(2, RoundingMode.HALF_UP);\n    }\n\n")
    lines.append("    BigDecimal ageLoading(int age) {\n")
    lines.append(f"        if (age < {age_bands[0]}) return new BigDecimal(\"{age_load[0]}\");\n")
    lines.append(f"        if (age < {age_bands[1]}) return new BigDecimal(\"{age_load[1]}\");\n")
    lines.append(f"        if (age < {age_bands[2]}) return new BigDecimal(\"{age_load[2]}\");\n")
    lines.append(f"        return new BigDecimal(\"{age_load[3]}\");\n    }}\n\n")
    lines.append("    @Override\n    public Optional<String> referralReason(RatingInput in) {\n")
    lines.append("        if (in.sumInsured().compareTo(MAX_SUM_INSURED) > 0) {\n"
                 f"            return Optional.of(\"Sum insured above the {label} limit of {max_si:,}\");\n        }}\n")
    lines.append("        if (in.priorClaims() >= REFER_PRIOR_CLAIMS) {\n"
                 "            return Optional.of(in.priorClaims() + \" prior claims (refer at \" + REFER_PRIOR_CLAIMS + \")\");\n        }\n")
    declines = []
    for name, value, reason in referrals:
        if reason:
            lines.append(f"        if (\"{value}\".equals(in.factors().get(\"{name}\"))) {{\n"
                         f"            return Optional.of(\"{reason}\");\n        }}\n")
        else:
            declines.append((name, value))
    lines.append("        return Optional.empty();\n    }\n\n")
    lines.append("    static String area(String postcode) {\n"
                 "        String outward = postcode == null ? \"\" : postcode.trim().split(\" \")[0];\n"
                 "        String letters = outward.replaceAll(\"[0-9].*$\", \"\");\n"
                 "        return AREA.containsKey(letters) ? letters : letters.isEmpty() ? \"\" : letters.substring(0, 1);\n    }\n")
    if declines:
        lines.append("\n    /** Risks priced but flagged for the next workbook review (no referral today). */\n")
        lines.append("    static boolean onWatchList(RatingInput in) {\n        return " + " || ".join(
            f"\"{v}\".equals(in.factors().get(\"{n}\"))" for n, v in declines) + ";\n    }\n")
    lines.append("}\n")
    w(J + f"{cls}RatingRules.java", "".join(lines))

    # test
    first_ref = next(((n, v, r) for n, v, r in referrals if r), None)
    si_ok = min(max_si // 4, 250000)
    t = [f"package com.corvane.policy.rating;\n\nimport com.corvane.policy.domain.ProductLine;\n"
         "import com.corvane.policy.domain.RatingInput;\nimport org.junit.jupiter.api.Test;\n\n"
         "import java.math.BigDecimal;\nimport java.util.Map;\n\nimport static org.assertj.core.api.Assertions.assertThat;\n\n",
         f"class {cls}RatingRulesTest {{\n\n    private final {cls}RatingRules rules = new {cls}RatingRules();\n\n",
         f"    private RatingInput input(BigDecimal sumInsured, int priorClaims, Map<String, String> factors) {{\n"
         f"        return new RatingInput(ProductLine.{code}, \"ZZ1 1AA\", 45, sumInsured, BigDecimal.ZERO, priorClaims, factors);\n    }}\n\n",
         "    @Test\n    void neverBelowMinimumPremium() {\n"
         "        assertThat(rules.basePremium(input(BigDecimal.ONE, 0, Map.of()))).isEqualByComparingTo(MINIMUM());\n    }\n\n",
         "    private static BigDecimal MINIMUM() { return " + f"{cls}RatingRules.MINIMUM_PREMIUM; }}\n\n",
         "    @Test\n    void priorClaimsLoadThePremium() {\n"
         f"        BigDecimal clean = rules.basePremium(input(new BigDecimal(\"{si_ok}\"), 0, Map.of()));\n"
         f"        BigDecimal one = rules.basePremium(input(new BigDecimal(\"{si_ok}\"), 1, Map.of()));\n"
         "        assertThat(one).isGreaterThanOrEqualTo(clean);\n    }\n\n",
         "    @Test\n    void refersAboveLineLimit() {\n"
         f"        assertThat(rules.referralReason(input(new BigDecimal(\"{max_si + 1}\"), 0, Map.of()))).isPresent();\n    }}\n\n",
         "    @Test\n    void refersOnPriorClaims() {\n"
         f"        assertThat(rules.referralReason(input(new BigDecimal(\"{si_ok}\"), {prior_refer}, Map.of()))).isPresent();\n"
         f"        assertThat(rules.referralReason(input(new BigDecimal(\"{si_ok}\"), {prior_refer - 1}, Map.of()))).isEmpty();\n    }}\n"]
    if first_ref:
        n, v, r = first_ref
        t.append(f"\n    @Test\n    void refers_{n}_{''.join(c if c.isalnum() else '_' for c in v)}() {{\n"
                 f"        assertThat(rules.referralReason(input(new BigDecimal(\"{si_ok}\"), 0, Map.of(\"{n}\", \"{v}\"))))"
                 f".contains(\"{r}\");\n    }}\n")
    t.append("}\n")
    body = "".join(t[1:]).replace(f"class {cls}RatingRulesTest {{", f"@Nested\nclass {cls} {{")
    body = "\n".join(("    " + ln) if ln.strip() else ln for ln in body.split("\n"))
    test_bodies.append(body)

    # liquibase factor rows
    rows = []
    for name, table in fac_tables.items():
        for opt, val in table:
            rows.append(f"              - column: {{ name: line_code, value: {code} }}\n"
                        f"              - column: {{ name: factor, value: {name} }}\n"
                        f"              - column: {{ name: option_value, value: \"{opt}\" }}\n"
                        f"              - column: {{ name: loading, valueNumeric: {val} }}\n")
    changesets.append(
        f"  - changeSet:\n      id: 010-factors-{code.lower()}\n      author: rating-workbook-export\n"
        f"      comment: \"{label} factor loadings from RW-{code}-2026Q3 (rate {rate}/1000)\"\n      changes:\n" +
        "".join(f"        - insert:\n            tableName: rating_factor\n            columns:\n{r}" for r in rows))

head = ("databaseChangeLog:\n  - changeSet:\n      id: 010-rating-factor-table\n      author: policy-core\n      changes:\n"
        "        - createTable:\n            tableName: rating_factor\n            remarks: \"Mirror of the Java factor maps, read by the underwriting console\"\n"
        "            columns:\n"
        "              - column: { name: line_code, type: CHAR(3), constraints: { nullable: false } }\n"
        "              - column: { name: factor, type: VARCHAR(40), constraints: { nullable: false } }\n"
        "              - column: { name: option_value, type: VARCHAR(40), constraints: { nullable: false } }\n"
        "              - column: { name: loading, type: DECIMAL(5,2), constraints: { nullable: false } }\n")
w(T + "AllLinesRatingRulesTest.java", "package com.corvane.policy.rating;\n\nimport com.corvane.policy.domain.ProductLine;\n"
  "import com.corvane.policy.domain.RatingInput;\nimport org.junit.jupiter.api.Nested;\nimport org.junit.jupiter.api.Test;\n\n"
  "import java.math.BigDecimal;\nimport java.util.Map;\n\nimport static org.assertj.core.api.Assertions.assertThat;\n\n"
  "/** Rating rules for all twelve product lines: minimum premium, prior-claims loading and referral triggers. */\n"
  "class AllLinesRatingRulesTest {\n\n" + "\n".join(test_bodies) + "}\n")
w(PA + "src/main/resources/db/changelog/changes/010-rating-factors.yaml", head + "".join(changesets))
print("policyadmin_gen done:", len(LINES), "lines")
