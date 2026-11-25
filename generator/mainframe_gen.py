"""Builder D bulk generator (seeded, deterministic) for the Corvane Mutual estate v2.

Writes:
  mainframe/cobol/RAT<line>01.cbl   one rating program per line of business (12), called dynamically by PRMCALC
  mainframe/cobol/PRMRULES.cbl      the underwriting rule table, ~4,000 lines (long-file / chunking test)
  data/postgres/010_ref_rate_bands.sql  dw.ref_rate_band, the same bands and rates the RAT programs use

Run: python3 -I generator/mainframe_gen.py <estate_root>
"""
import os
import random
import sys

ROOT = sys.argv[1]
RNG = random.Random(20261116)
ERRORS = []


def cobol(name, lines):
    out = []
    for i, line in enumerate(lines, 1):
        line = line.rstrip() or " "
        if len(line) > 66:
            ERRORS.append(f"{name} line {i}: {line!r}")
        out.append(f"{i * 100:06d}{line}")
    return "\n".join(out) + "\n"


def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


# Per line: title, sum-insured scale (band upper bounds), rate range, minimum premium, risk-detail fields.
# Field kinds: over (num > t loads), under (num < t loads), yes (flag Y loads), yesdisc (flag Y discounts),
# code (letter codes load differently), perunit (discount per unit up to a cap).
LINES = {
    "MTR": ("MOTOR", [8000, 20000, 45000, 90000], (0.018, 0.062), 145, [
        ("VEH-GROUP", "9(02)", "over", 38), ("DRIVER-AGE", "9(02)", "under", 25),
        ("NCD-YEARS", "9(02)", "perunit", 9), ("ANNUAL-MILES", "9(06)", "over", 15000),
        ("GARAGED", "X(01)", "yesdisc", None), ("USE-CLASS", "X(01)", "code", "SCB")]),
    "HOM": ("HOME BUILDINGS", [150000, 350000, 750000, 1500000], (0.0009, 0.0031), 120, [
        ("BUILD-YEAR", "9(04)", "under", 1920), ("BEDROOMS", "9(02)", "over", 5),
        ("FLOOD-ZONE", "9(01)", "over", 2), ("SUBSIDENCE", "X(01)", "yes", None),
        ("ROOF-TYPE", "X(01)", "code", "TSF"), ("LISTED", "X(01)", "yes", None)]),
    "CNT": ("HOME CONTENTS", [25000, 60000, 120000], (0.0035, 0.0090), 65, [
        ("HIGH-RISK-ITEMS", "9(02)", "over", 4), ("ALARM", "X(01)", "yesdisc", None),
        ("UNOCCUPIED-DAYS", "9(03)", "over", 30), ("STUDENT-LET", "X(01)", "yes", None)]),
    "TRV": ("TRAVEL", [5000, 10000, 25000], (0.0040, 0.0150), 18, [
        ("TRIP-TYPE", "X(01)", "code", "SAM"), ("DEST-ZONE", "9(01)", "over", 2),
        ("MAX-TRIP-DAYS", "9(03)", "over", 31), ("TRAVELLERS", "9(02)", "over", 4),
        ("WINTER-SPORTS", "X(01)", "yes", None), ("OLDEST-AGE", "9(02)", "over", 70)]),
    "PET": ("PET", [2000, 4000, 7000, 12000], (0.030, 0.085), 60, [
        ("SPECIES", "X(01)", "code", "DCR"), ("BREED-BAND", "9(01)", "over", 3),
        ("PET-AGE", "9(02)", "over", 8), ("PRE-EXISTING", "X(01)", "yes", None),
        ("NEUTERED", "X(01)", "yesdisc", None)]),
    "LLD": ("LANDLORD", [200000, 500000, 1200000], (0.0011, 0.0034), 160, [
        ("UNITS", "9(03)", "over", 6), ("TENANT-TYPE", "X(01)", "code", "PSB"),
        ("RENT-GUARANTEE", "X(01)", "yes", None), ("HMO", "X(01)", "yes", None),
        ("VACANT-UNITS", "9(03)", "over", 1)]),
    "MAR": ("MARINE CARGO", [250000, 1000000, 5000000], (0.0012, 0.0045), 450, [
        ("CARGO-CLASS", "9(02)", "over", 12), ("VOYAGE-ZONE", "9(01)", "over", 3),
        ("REFRIGERATED", "X(01)", "yes", None), ("WAR-RISK", "X(01)", "yes", None),
        ("CONTAINERISED", "X(01)", "yesdisc", None)]),
    "CPR": ("COMMERCIAL PROPERTY", [500000, 2000000, 10000000], (0.0008, 0.0029), 350, [
        ("CONSTRUCTION", "X(01)", "code", "ABC"), ("SPRINKLERED", "X(01)", "yesdisc", None),
        ("TRADE-CODE", "9(04)", "over", 7000), ("FLOOR-AREA", "9(07)", "over", 20000),
        ("VACANT", "X(01)", "yes", None)]),
    "PLB": ("PUBLIC LIABILITY", [1000000, 2000000, 5000000, 10000000], (0.00025, 0.0011), 140, [
        ("TURNOVER-K", "9(07)", "over", 2500), ("TRADE-RISK", "9(01)", "over", 3),
        ("EMPLOYEES", "9(04)", "over", 50), ("CLAIMS-5Y", "9(02)", "over", 1),
        ("WORK-AT-HEIGHT", "X(01)", "yes", None)]),
    "PIN": ("PROFESSIONAL INDEMNITY", [250000, 1000000, 5000000], (0.0012, 0.0060), 300, [
        ("PROFESSION", "X(01)", "code", "ALM"), ("FEE-INCOME-K", "9(07)", "over", 1500),
        ("YEARS-TRADING", "9(02)", "under", 3), ("US-WORK", "X(01)", "yes", None),
        ("QUALIFIED", "X(01)", "yesdisc", None)]),
    "CYB": ("CYBER", [250000, 1000000, 3000000], (0.0030, 0.0140), 400, [
        ("REVENUE-K", "9(07)", "over", 10000), ("RECORDS-K", "9(06)", "over", 500),
        ("MFA", "X(01)", "yesdisc", None), ("SECTOR", "X(01)", "code", "HFR"),
        ("BACKUPS-OFFLINE", "X(01)", "yesdisc", None), ("PRIOR-BREACH", "X(01)", "yes", None)]),
    "GDG": ("GADGET", [500, 1200, 2500], (0.060, 0.140), 36, [
        ("DEVICE-TYPE", "X(01)", "code", "PTL"), ("DEVICE-AGE-MO", "9(02)", "over", 24),
        ("ACCIDENTAL-DMG", "X(01)", "yes", None), ("LOSS-COVER", "X(01)", "yes", None)]),
}


DESC = {
    "VEH-GROUP": "VEHICLE GROUP 01-50, REFER ABOVE 3X THRESHOLD",
    "DRIVER-AGE": "YOUNGEST NAMED DRIVER, YEARS",
    "NCD-YEARS": "NO-CLAIMS DISCOUNT YEARS, CAPPED AT 9",
    "ANNUAL-MILES": "DECLARED ANNUAL MILEAGE",
    "GARAGED": "Y = KEPT IN A LOCKED GARAGE OVERNIGHT",
    "USE-CLASS": "S SOCIAL, C COMMUTING, B BUSINESS",
    "BUILD-YEAR": "YEAR THE PROPERTY WAS BUILT",
    "BEDROOMS": "NUMBER OF BEDROOMS",
    "FLOOD-ZONE": "1 LOW TO 3 HIGH (SEE postcodes-latin1.csv)",
    "SUBSIDENCE": "Y = HISTORY OF SUBSIDENCE",
    "ROOF-TYPE": "T TILE, S SLATE, F FLAT",
    "LISTED": "Y = LISTED BUILDING",
    "HIGH-RISK-ITEMS": "ITEMS OVER 2,000 EACH",
    "ALARM": "Y = MONITORED ALARM",
    "UNOCCUPIED-DAYS": "LONGEST PERIOD EMPTY, DAYS PER YEAR",
    "STUDENT-LET": "Y = LET TO STUDENTS",
    "TRIP-TYPE": "S SINGLE, A ANNUAL MULTI-TRIP, M MULTI-TRIP",
    "DEST-ZONE": "1 UK, 2 EUROPE, 3 WORLDWIDE EX USA, 4 USA",
    "MAX-TRIP-DAYS": "LONGEST TRIP, DAYS",
    "TRAVELLERS": "NUMBER OF TRAVELLERS",
    "WINTER-SPORTS": "Y = WINTER SPORTS COVER",
    "OLDEST-AGE": "AGE OF THE OLDEST TRAVELLER",
    "SPECIES": "D DOG, C CAT, R RABBIT",
    "BREED-BAND": "BREED RISK BAND 1-5",
    "PET-AGE": "AGE IN YEARS",
    "PRE-EXISTING": "Y = DECLARED PRE-EXISTING CONDITION",
    "NEUTERED": "Y = NEUTERED",
    "UNITS": "LETTABLE UNITS",
    "TENANT-TYPE": "P PROFESSIONAL, S STUDENT, B BENEFITS",
    "RENT-GUARANTEE": "Y = RENT GUARANTEE COVER",
    "HMO": "Y = HOUSE IN MULTIPLE OCCUPATION",
    "VACANT-UNITS": "UNITS EMPTY TODAY",
    "CARGO-CLASS": "INSTITUTE CARGO CLASS 01-20",
    "VOYAGE-ZONE": "1 COASTAL TO 4 HIGH-RISK WATERS",
    "REFRIGERATED": "Y = REEFER CARGO",
    "WAR-RISK": "Y = WAR AND STRIKES COVER",
    "CONTAINERISED": "Y = CONTAINERISED",
    "CONSTRUCTION": "A NON-COMBUSTIBLE, B MIXED, C COMBUSTIBLE",
    "SPRINKLERED": "Y = SPRINKLERS FITTED",
    "TRADE-CODE": "SIC-STYLE TRADE CODE",
    "FLOOR-AREA": "SQUARE METRES",
    "VACANT": "Y = PREMISES VACANT",
    "TURNOVER-K": "ANNUAL TURNOVER, THOUSANDS",
    "TRADE-RISK": "TRADE RISK BAND 1-5",
    "EMPLOYEES": "HEADCOUNT",
    "CLAIMS-5Y": "LIABILITY CLAIMS IN 5 YEARS",
    "WORK-AT-HEIGHT": "Y = WORK ABOVE 3 METRES",
    "PROFESSION": "A ACCOUNTANT, L LAWYER, M MANAGEMENT CONSULTANT",
    "FEE-INCOME-K": "FEE INCOME, THOUSANDS",
    "YEARS-TRADING": "YEARS IN BUSINESS",
    "US-WORK": "Y = ANY WORK FOR US CLIENTS",
    "QUALIFIED": "Y = CHARTERED / QUALIFIED",
    "REVENUE-K": "ANNUAL REVENUE, THOUSANDS",
    "RECORDS-K": "PERSONAL RECORDS HELD, THOUSANDS",
    "MFA": "Y = MFA ON ALL REMOTE ACCESS",
    "SECTOR": "H HEALTH, F FINANCE, R RETAIL",
    "BACKUPS-OFFLINE": "Y = OFFLINE BACKUPS TESTED",
    "PRIOR-BREACH": "Y = BREACH IN LAST 3 YEARS",
    "DEVICE-TYPE": "P PHONE, T TABLET, L LAPTOP",
    "DEVICE-AGE-MO": "DEVICE AGE, MONTHS",
    "ACCIDENTAL-DMG": "Y = ACCIDENTAL DAMAGE COVER",
    "LOSS-COVER": "Y = LOSS AND THEFT COVER",
}


def pic_len(pic):
    return int(pic[pic.index("(") + 1:pic.index(")")])


def pct():
    return RNG.choice([0.025, 0.04, 0.05, 0.075, 0.10, 0.125, 0.15, 0.20, 0.25])


def rat_program(code):
    title, bounds, (lo, hi), minprem, fields = LINES[code]
    rates = sorted((round(RNG.uniform(lo, hi), 5) for _ in bounds), reverse=True)
    bands = []
    prev = 0
    for i, (ub, rate) in enumerate(zip(bounds, rates), 1):
        bands.append((f"B{i}", prev, ub, rate))
        prev = ub
    name = f"RAT{code}01"
    used = sum(pic_len(p) for _, p, _, _ in fields)
    L = [
        " IDENTIFICATION DIVISION.",
        f" PROGRAM-ID. {name}.",
        " AUTHOR. CORVANE UNDERWRITING SYSTEMS.",
        "*" + "=" * 64,
        f"* {name}  {title} RATING",
        f"* CALLED BY PRMCALC (BATCH) AND PRMCALC0 (CICS) AS 'RAT{code}01'.",
        "* SETS RATE-BASE-PREMIUM FROM THE SUM-INSURED BAND, THEN ADDS",
        "* LINE LOADINGS AND DISCOUNTS FROM THE 60-BYTE RISK DETAIL.",
        "* BANDS AND RATES ARE THE SAME AS dw.ref_rate_band IN claimsdb.",
        "*" + "=" * 64,
        " DATA DIVISION.",
        " WORKING-STORAGE SECTION.",
        f"     COPY RD{code}.",
    ]
    C = ["*" + "=" * 64,
         f"* RD{code}  {title} RISK DETAIL",
         f"*        THE 60-BYTE POL-RISK-DETAIL OF POLREC FOR LINE {code}.",
         f"*        USED BY RAT{code}01.",
         "*        policy-admin FILLS THE SAME 60 BYTES IN PRMCOMM",
         "*        REQ-RISK-DETAIL WHEN IT CALLS PRMCALC0.",
         "*"]
    for fname, pic, kind, arg in fields:
        C.append(f"*  {fname:<16}{DESC.get(fname, '')}"[:66])
    C += ["*" + "=" * 64, f" 01  WS-{code}-DETAIL."]
    for fname, pic, _, _ in fields:
        C.append(f"     05  WS-{fname:<22}PIC {pic}.")
    C.append(f"     05  FILLER                  PIC X({60 - used:02d}).")
    write(f"mainframe/copybooks/RD{code}.cpy", cobol(f"RD{code}", C))
    L += [
        " 01  WS-BAND                     PIC X(02).",
        " 01  WS-PCT                      PIC 9V9999.",
        " LINKAGE SECTION.",
        "     COPY POLREC.",
        "     COPY RATEREC.",
        " PROCEDURE DIVISION USING POL-RECORD RATE-RECORD.",
        " 0000-MAIN.",
        f"     MOVE POL-RISK-DETAIL TO WS-{code}-DETAIL",
        "     PERFORM 1000-BASE-RATE",
        "     PERFORM 2000-LOADINGS",
        "     MOVE ZERO TO RATE-RETURN-CODE",
        "     GOBACK.",
        " 1000-BASE-RATE.",
        "     EVALUATE TRUE",
    ]
    for band, _, ub, rate in bands:
        L += [
            f"         WHEN POL-SUM-INSURED <= {ub}",
            f"             MOVE '{band}' TO WS-BAND",
            "             COMPUTE RATE-BASE-PREMIUM ROUNDED =",
            f"                 POL-SUM-INSURED * {rate:.5f}",
        ]
    top = bands[-1]
    L += [
        "         WHEN OTHER",
        "*            ABOVE THE TOP BAND: RATE AT THE TOP BAND, REFER",
        "             MOVE 'XX' TO WS-BAND",
        "             COMPUTE RATE-BASE-PREMIUM ROUNDED =",
        f"                 POL-SUM-INSURED * {top[3]:.5f}",
        "             SET RATE-REFER TO TRUE",
        "     END-EVALUATE",
        f"     IF RATE-BASE-PREMIUM < {minprem}.00",
        f"         MOVE {minprem}.00 TO RATE-BASE-PREMIUM",
        "     END-IF.",
        " 2000-LOADINGS.",
    ]
    for fname, pic, kind, arg in fields:
        f = f"WS-{fname}"
        p = pct()
        if kind == "over":
            L += [f"     IF {f} > {arg}",
                  "         COMPUTE RATE-LOADINGS ROUNDED = RATE-LOADINGS",
                  f"             + RATE-BASE-PREMIUM * {p:.3f}",
                  "     END-IF"]
            if RNG.random() < 0.5:
                L += [f"     IF {f} > {arg * 3}",
                      "         SET RATE-REFER TO TRUE",
                      "     END-IF"]
        elif kind == "under":
            L += [f"     IF {f} < {arg} AND {f} > ZERO",
                  "         COMPUTE RATE-LOADINGS ROUNDED = RATE-LOADINGS",
                  f"             + RATE-BASE-PREMIUM * {p:.3f}",
                  "     END-IF"]
        elif kind == "yes":
            L += [f"     IF {f} = 'Y'",
                  "         COMPUTE RATE-LOADINGS ROUNDED = RATE-LOADINGS",
                  f"             + RATE-BASE-PREMIUM * {p:.3f}",
                  "     END-IF"]
        elif kind == "yesdisc":
            L += [f"     IF {f} = 'Y'",
                  "         COMPUTE RATE-DISCOUNTS ROUNDED = RATE-DISCOUNTS",
                  f"             + RATE-BASE-PREMIUM * {p:.3f}",
                  "     END-IF"]
        elif kind == "perunit":
            unit = RNG.choice([0.03, 0.04, 0.05])
            L += [f"     IF {f} > {arg}",
                  f"         MOVE {arg} TO {f}",
                  "     END-IF",
                  f"     COMPUTE WS-PCT = {f} * {unit:.2f}",
                  "     COMPUTE RATE-DISCOUNTS ROUNDED = RATE-DISCOUNTS",
                  "         + RATE-BASE-PREMIUM * WS-PCT"]
        elif kind == "code":
            L.append(f"     EVALUATE {f}")
            for i, letter in enumerate(arg):
                lp = round(0.05 * i + RNG.choice([0.0, 0.025, 0.05]), 3)
                L.append(f"         WHEN '{letter}'")
                if lp == 0:
                    L.append("             CONTINUE")
                else:
                    L += ["             COMPUTE RATE-LOADINGS ROUNDED =",
                          f"                 RATE-LOADINGS + RATE-BASE-PREMIUM * {lp:.3f}"]
            L += ["         WHEN OTHER",
                  "             SET RATE-REFER TO TRUE",
                  "     END-EVALUATE"]
    L[-1] = L[-1] + "."
    write(f"mainframe/cobol/{name}.cbl", cobol(name, L))
    return bands, minprem


# ---------------------------------------------------------------- PRMRULES
CONDS = [
    ("POL-RISK-SCORE > {n}", lambda: RNG.randrange(450, 840, 7), "RISK SCORE ABOVE {n}"),
    ("WS-INSURED-AGE < {n}", lambda: RNG.choice([21, 23, 25, 28, 30]), "INSURED UNDER {n}"),
    ("WS-INSURED-AGE > {n}", lambda: RNG.choice([65, 70, 75, 80]), "INSURED OVER {n}"),
    ("POL-REGION-US", None, "US POLICY"),
    ("POL-REGION-UK", None, "UK POLICY"),
    ("POL-BILL-MONTHLY", None, "PAYS MONTHLY"),
    ("POL-VOLUNTARY-EXCESS >= {n}", lambda: RNG.choice([250, 500, 1000, 2500]), "VOLUNTARY EXCESS {n}+"),
    ("WS-POLICY-YEARS > {n}", lambda: RNG.choice([2, 3, 5, 8, 10]), "LOYAL MORE THAN {n} YEARS"),
    ("WS-START-MONTH = {n}", lambda: RNG.randint(1, 12), "INCEPTION MONTH {n}"),
    ("INSURED-POSTCODE(1:2) = '{s}'", lambda: RNG.choice(["CV", "CW", "87", "81", "95", "33", "70"]),
     "POSTCODE AREA {s}"),
    ("POL-BROKER-ID(1:2) = '{s}'", lambda: RNG.choice(["BK", "DI", "AG", "PW"]), "CHANNEL {s}"),
]


def cond_text():
    k = 1 if RNG.random() < 0.55 else 2
    picks = RNG.sample(CONDS, k)
    code, why = [], []
    for expr, gen, label in picks:
        v = gen() if gen else None
        code.append(expr.format(n=v, s=v))
        why.append(label.format(n=v, s=v))
    return code, " AND ".join(why)


def rule(code, n, lines_out, memo_years):
    rid = f"{code}{n:03d}"
    conds, why = cond_text()
    memo = f"UW-{RNG.choice(memo_years)}-{RNG.randint(10, 199):03d}"
    roll = RNG.random()
    lines_out.append(f" {code}-{n:04d}.")
    lines_out.append(f"*    {rid} {memo}: {why}"[:66])
    lines_out.append(f"     IF {conds[0]}")
    for c in conds[1:]:
        lines_out.append(f"        AND {c}")
    if roll < 0.62:
        lines_out += ["         COMPUTE RATE-LOADINGS ROUNDED = RATE-LOADINGS",
                      f"             + RATE-BASE-PREMIUM * {pct():.3f}"]
    elif roll < 0.92:
        lines_out += ["         COMPUTE RATE-DISCOUNTS ROUNDED = RATE-DISCOUNTS",
                      f"             + RATE-BASE-PREMIUM * {RNG.choice([0.02, 0.03, 0.05, 0.075]):.3f}"]
    else:
        lines_out.append("         SET RATE-REFER TO TRUE")
    lines_out += ["         ADD 1 TO RATE-RULES-FIRED",
                  f"         MOVE '{rid}' TO RATE-LAST-RULE",
                  "     END-IF."]


def prmrules(rules_per_line):
    L = [
        " IDENTIFICATION DIVISION.",
        " PROGRAM-ID. PRMRULES.",
        " AUTHOR. CORVANE UNDERWRITING SYSTEMS.",
        "*" + "=" * 64,
        "* PRMRULES  UNDERWRITING RULE TABLE",
        "*",
        "* CALLED BY PRMCALC (BATCH) AND PRMCALC0 (CICS) AFTER THE LINE'S",
        "* RAT<LINE>01 PROGRAM HAS SET THE BASE PREMIUM. EACH RULE IS ONE",
        "* PARAGRAPH; THE SECTION FOR THE POLICY'S LINE RUNS EVERY RULE IN",
        "* ORDER. A RULE THAT FIRES ADDS A LOADING OR A DISCOUNT, OR SETS",
        "* THE REFER FLAG, AND RECORDS ITS ID IN RATE-LAST-RULE.",
        "* 9000-CAPS LIMITS LOADINGS TO 150% AND DISCOUNTS TO 40% OF BASE.",
        "* RULES IN RETIRED-RULES ARE NEVER PERFORMED. THEY ARE KEPT",
        "* BECAUSE AUDIT ASKED FOR THE HISTORY (2022).",
        "* MEMO IDS (UW-YYYY-NNN) ARE UNDERWRITING COMMITTEE DECISIONS.",
        "*" + "=" * 64,
        " DATA DIVISION.",
        " WORKING-STORAGE SECTION.",
        " 01  WS-INSURED-AGE              PIC 9(03).",
        " 01  WS-POLICY-YEARS             PIC 9(03).",
        " 01  WS-START-MONTH              PIC 9(02).",
        " 01  WS-DATE-X.",
        "     05  WS-DATE-CCYY            PIC 9(04).",
        "     05  WS-DATE-MM              PIC 9(02).",
        "     05  WS-DATE-DD              PIC 9(02).",
        " 01  WS-DATE-N REDEFINES WS-DATE-X PIC 9(08).",
        " 01  WS-MAX-LOAD                 PIC S9(07)V99 COMP-3.",
        " 01  WS-MAX-DISC                 PIC S9(07)V99 COMP-3.",
        " LINKAGE SECTION.",
        "     COPY POLREC.",
        "     COPY RATEREC.",
        " PROCEDURE DIVISION USING POL-RECORD RATE-RECORD.",
        " 0000-MAIN SECTION.",
        " 0000-START.",
        "     PERFORM 0500-DERIVE",
        "     EVALUATE POL-LINE-CODE",
    ]
    for code in LINES:
        L += [f"         WHEN '{code}'", f"             PERFORM {code}-RULES"]
    L += [
        "         WHEN OTHER",
        "             CONTINUE",
        "     END-EVALUATE",
        "     PERFORM 9000-CAPS",
        "     GOBACK.",
        " 0500-DERIVE SECTION.",
        " 0500-START.",
        "     COMPUTE WS-INSURED-AGE =",
        "         (RATE-BILL-DATE - INSURED-DOB) / 10000",
        "     MOVE POL-START-DATE TO WS-DATE-N",
        "     MOVE WS-DATE-MM TO WS-START-MONTH",
        "     IF POL-START-DATE > ZERO",
        "         COMPUTE WS-POLICY-YEARS =",
        "             (RATE-BILL-DATE - POL-START-DATE) / 10000",
        "     ELSE",
        "         MOVE ZERO TO WS-POLICY-YEARS",
        "     END-IF.",
    ]
    for code, (title, *_rest) in LINES.items():
        L += [f" {code}-RULES SECTION.", f"*    {title} RULES"]
        for n in range(1, rules_per_line + 1):
            rule(code, n, L, [2016, 2018, 2019, 2021, 2022, 2023, 2024, 2025])
    L += [
        " 9000-CAPS SECTION.",
        " 9000-START.",
        "     COMPUTE WS-MAX-LOAD = RATE-BASE-PREMIUM * 1.5",
        "     COMPUTE WS-MAX-DISC = RATE-BASE-PREMIUM * 0.4",
        "     IF RATE-LOADINGS > WS-MAX-LOAD",
        "         MOVE WS-MAX-LOAD TO RATE-LOADINGS",
        "     END-IF",
        "     IF RATE-DISCOUNTS > WS-MAX-DISC",
        "         MOVE WS-MAX-DISC TO RATE-DISCOUNTS",
        "     END-IF.",
        " RETIRED-RULES SECTION.",
        "*    NOT PERFORMED FROM ANYWHERE. KEPT FOR AUDIT HISTORY.",
    ]
    for code in LINES:
        for n in range(901, 903):
            rule(code, n, L, [2012, 2013, 2014, 2015])
    write("mainframe/cobol/PRMRULES.cbl", cobol("PRMRULES", L))
    return len(L)


bands_by_line = {code: rat_program(code) for code in LINES}
rules_per_line = int(os.environ.get("PRMRULES_PER_LINE", "40"))
n_lines = prmrules(rules_per_line)

sql = ["-- dw.ref_rate_band: base rating bands by line of business.",
       "-- Generated from the same table as mainframe/cobol/RAT<line>01.cbl, so the two always agree.",
       "-- Used by finance to re-rate samples of the nightly billing.",
       "",
       "CREATE TABLE IF NOT EXISTS dw.ref_rate_band (",
       "    line_code       char(3) NOT NULL,",
       "    band            char(2) NOT NULL,",
       "    si_from         numeric(13,2) NOT NULL,",
       "    si_to           numeric(13,2) NOT NULL,",
       "    rate            numeric(8,5) NOT NULL,",
       "    min_premium     numeric(9,2) NOT NULL,",
       "    rating_program  varchar(8) NOT NULL,",
       "    PRIMARY KEY (line_code, band)",
       ");",
       "",
       "INSERT INTO dw.ref_rate_band (line_code, band, si_from, si_to, rate, min_premium, rating_program) VALUES"]
rows = []
for code, (bands, minprem) in bands_by_line.items():
    for band, frm, to, rate in bands:
        rows.append(f"  ('{code}', '{band}', {frm}, {to}, {rate:.5f}, {minprem}.00, 'RAT{code}01')")
sql.append(",\n".join(rows) + ";")
write("data/postgres/010_ref_rate_bands.sql", "\n".join(sql) + "\n")

if ERRORS:
    raise SystemExit("lines past column 72:\n" + "\n".join(ERRORS[:30]))
print(f"generated 12 rating programs, PRMRULES with {n_lines} lines")
