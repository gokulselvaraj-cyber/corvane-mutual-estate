"""Builder E bulk generator: per-product-line portal quote forms, product guides, help pages and the minified
portal bundle. Seeded and deterministic. Run: python3 -I docs_gen.py <estate_root>"""
import os, random, sys

ROOT = sys.argv[1]
rng = random.Random(20261116)


def W(path, text):
    p = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text.lstrip("\n"))


# code, name, component, region, fields (name, type, label, rule), exclusions, extras, max cover
LINES = [
    ("MTR", "Motor", "MotorQuoteForm", "UK+US",
     [("vehicleRegistration", "string", "Vehicle registration", "regex:^[A-Z0-9 ]{2,8}$"),
      ("vehicleValue", "number", "Vehicle value", "range:500:150000"),
      ("annualMileage", "number", "Annual mileage", "range:1000:50000"),
      ("mainDriverAge", "number", "Main driver age", "range:17:99"),
      ("overnightParking", "enum:DRIVEWAY|GARAGE|STREET", "Where is it kept overnight?", "required")],
     ["Racing or track days", "Wear and tear", "Driving without a valid licence"],
     ["Breakdown cover", "Courtesy car", "Legal expenses"], 150000),
    ("HOM", "Home buildings", "HomeBuildingsQuoteForm", "UK",
     [("rebuildCost", "number", "Rebuild cost", "range:50000:2500000"),
      ("yearBuilt", "number", "Year built", "range:1600:2026"),
      ("roofType", "enum:STANDARD|FLAT|THATCH", "Roof type", "required"),
      ("listedBuilding", "boolean", "Is it a listed building?", "none"),
      ("floodHistory", "boolean", "Has the property flooded in the last 10 years?", "none")],
     ["Gradual deterioration", "Subsidence in the first 12 months", "Unoccupied over 60 days"],
     ["Accidental damage", "Home emergency"], 2500000),
    ("CNT", "Home contents", "ContentsQuoteForm", "UK",
     [("contentsValue", "number", "Total contents value", "range:5000:250000"),
      ("highRiskItemsValue", "number", "Jewellery, watches and art", "range:0:100000"),
      ("lockType", "enum:BS3621|OTHER", "Front door lock", "required"),
      ("alarm", "boolean", "Burglar alarm fitted?", "none")],
     ["Items left in an unlocked car", "Money over £500", "Pets damaging contents"],
     ["Personal possessions away from home", "Bicycle cover"], 250000),
    ("TRV", "Travel", "TravelQuoteForm", "UK+US",
     [("tripType", "enum:SINGLE|ANNUAL", "Single trip or annual", "required"),
      ("destination", "enum:EUROPE|WORLDWIDE_EX_US|WORLDWIDE", "Destination", "required"),
      ("travellers", "number", "Number of travellers", "range:1:10"),
      ("oldestTravellerAge", "number", "Age of the oldest traveller", "range:0:85"),
      ("preExistingConditions", "boolean", "Any pre-existing medical conditions?", "none")],
     ["Travel against government advice", "Winter sports unless added", "Undeclared medical conditions"],
     ["Winter sports", "Gadget cover abroad"], 10000000),
    ("PET", "Pet", "PetQuoteForm", "UK",
     [("species", "enum:DOG|CAT|RABBIT", "Species", "required"),
      ("breed", "string", "Breed", "required"),
      ("ageYears", "number", "Age in years", "range:0:14"),
      ("microchipped", "boolean", "Microchipped?", "none")],
     ["Pre-existing conditions", "Routine vaccinations", "Pregnancy"],
     ["Lifetime cover", "Overseas travel"], 15000),
    ("LLD", "Landlord", "LandlordQuoteForm", "UK",
     [("propertiesCount", "number", "Number of let properties", "range:1:20"),
      ("tenantType", "enum:WORKING|STUDENT|DSS|HOLIDAY", "Tenant type", "required"),
      ("rentPerMonth", "number", "Rent per month", "range:200:20000"),
      ("hmo", "boolean", "House in multiple occupation?", "none")],
     ["Malicious damage by tenants unless added", "Unoccupied over 30 days"],
     ["Rent guarantee", "Malicious damage by tenants"], 2000000),
    ("MAR", "Marine cargo", "MarineCargoQuoteForm", "UK+US",
     [("cargoType", "enum:GENERAL|REFRIGERATED|HAZARDOUS", "Cargo type", "required"),
      ("annualShippedValue", "number", "Annual shipped value", "range:50000:50000000"),
      ("conveyance", "enum:SEA|AIR|ROAD", "Main conveyance", "required"),
      ("incoterm", "enum:FOB|CIF|DAP|DDP", "Usual Incoterm", "required")],
     ["Inherent vice", "Insufficient packing", "Delay"],
     ["War and strikes", "Storage up to 60 days"], 5000000),
    ("CPR", "Commercial property", "CommercialPropertyQuoteForm", "UK+US",
     [("occupancy", "enum:OFFICE|RETAIL|WAREHOUSE|LIGHT_INDUSTRIAL", "Occupancy", "required"),
      ("buildingSumInsured", "number", "Buildings sum insured", "range:100000:50000000"),
      ("sprinklers", "boolean", "Sprinklers fitted?", "none"),
      ("businessInterruptionMonths", "number", "Business interruption period (months)", "range:0:36")],
     ["Flood in high-risk zones unless agreed", "Cyber events"],
     ["Business interruption", "Terrorism"], 50000000),
    ("PLB", "Public liability", "PublicLiabilityQuoteForm", "UK+US",
     [("trade", "string", "Trade or business", "required"),
      ("annualTurnover", "number", "Annual turnover", "range:10000:20000000"),
      ("employees", "number", "Number of employees", "range:0:500"),
      ("limitOfIndemnity", "enum:1000000|2000000|5000000|10000000", "Limit of indemnity", "required")],
     ["Professional advice", "Work at heights over 15m unless declared"],
     ["Employers' liability", "Product liability"], 10000000),
    ("PIN", "Professional indemnity", "ProfessionalIndemnityQuoteForm", "UK+US",
     [("profession", "enum:ACCOUNTANT|ARCHITECT|CONSULTANT|IT_CONTRACTOR|SURVEYOR", "Profession", "required"),
      ("feeIncome", "number", "Annual fee income", "range:10000:10000000"),
      ("claimsLast5Years", "number", "Claims in the last 5 years", "range:0:10"),
      ("limitOfIndemnity", "enum:250000|500000|1000000|5000000", "Limit of indemnity", "required")],
     ["Known circumstances before inception", "Fines and penalties"],
     ["Run-off cover", "Defamation"], 5000000),
    ("CYB", "Cyber", "CyberQuoteForm", "UK+US",
     [("annualRevenue", "number", "Annual revenue", "range:100000:250000000"),
      ("recordsHeld", "number", "Personal data records held", "range:0:50000000"),
      ("mfaEnforced", "boolean", "Is MFA enforced for all remote access?", "required-true"),
      ("offlineBackups", "boolean", "Are backups kept offline?", "none")],
     ["Unpatched critical vulnerabilities over 30 days", "War and state-backed attacks", "Infrastructure outages"],
     ["Ransom negotiation", "Social engineering fraud"], 10000000),
    ("GDG", "Gadget", "GadgetQuoteForm", "UK",
     [("deviceType", "enum:PHONE|TABLET|LAPTOP|WATCH|HEADPHONES", "Device type", "required"),
      ("purchasePrice", "number", "Purchase price", "range:50:4000"),
      ("purchaseDate", "date", "Purchase date", "max-age-days:540")],
     ["Cosmetic damage", "Unattended in public", "Devices over 18 months old at purchase"],
     ["Worldwide cover", "Unauthorised call cover"], 4000),
]

P = "web/customer-portal/src/quote/"
W(P + "lines.ts", "import type { LineCode } from \"../model/Policy\";\n\nexport const LINES: { code: LineCode; name: string; region: string }[] = [\n"
  + "".join(f"  {{ code: \"{c}\", name: \"{n}\", region: \"{r}\" }},\n" for c, n, _, r, *_ in LINES) + "];\n")
W(P + "forms.ts", "import type { ComponentType } from \"react\";\nimport type { QuoteRequest } from \"../api/policyApi\";\nimport type { LineCode } from \"../model/Policy\";\n"
  + "".join(f"import {{ {comp} }} from \"./forms/{comp}\";\n" for _, _, comp, *_ in LINES)
  + "\nexport type QuoteFormProps = { onSubmit: (req: QuoteRequest) => void };\n\n"
  + "export const FORMS: Record<LineCode, ComponentType<QuoteFormProps>> = {\n"
  + "".join(f"  {c}: {comp},\n" for c, _, comp, *_ in LINES) + "};\n")


def ts_check(name, typ, rule):
    if rule.startswith("range:"):
        _, lo, hi = rule.split(":")
        return f"  if (!(Number(a.{name}) >= {lo} && Number(a.{name}) <= {hi})) e.push(\"{name} must be between {lo} and {hi}\");\n"
    if rule.startswith("regex:"):
        return f"  if (!/{rule[6:]}/.test(String(a.{name} ?? \"\"))) e.push(\"{name} is not valid\");\n"
    if rule == "required":
        return f"  if (a.{name} === undefined || a.{name} === \"\") e.push(\"{name} is required\");\n"
    if rule == "required-true":
        return f"  if (a.{name} !== true) e.push(\"We can only quote when {name} is in place\");\n"
    if rule.startswith("max-age-days:"):
        d = rule.split(":")[1]
        return f"  if ((Date.now() - new Date(String(a.{name})).getTime()) / 86400000 > {d}) e.push(\"{name}: devices must be under {d} days old\");\n"
    return ""


def ts_input(name, typ, label):
    if typ.startswith("enum:"):
        opts = "".join(f"<option>{o}</option>" for o in typ[5:].split("|"))
        return f"      <label>{label} <select onChange={{(ev) => set(\"{name}\", ev.target.value)}}><option value=\"\" />{opts}</select></label>\n"
    if typ == "boolean":
        return f"      <label><input type=\"checkbox\" onChange={{(ev) => set(\"{name}\", ev.target.checked)}} /> {label}</label>\n"
    kind = {"number": "number", "date": "date"}.get(typ, "text")
    conv = "Number(ev.target.value)" if typ == "number" else "ev.target.value"
    return f"      <label>{label} <input type=\"{kind}\" onChange={{(ev) => set(\"{name}\", {conv})}} /></label>\n"


for code, name, comp, region, fields, excl, extras, maxcover in LINES:
    volx = sorted(rng.sample([0, 100, 150, 200, 250, 300, 400, 500, 750, 1000], 4))
    referral = rng.choice(fields)[0]
    W(P + f"forms/{comp}.tsx", f"""
import {{ useState }} from "react";
import {{ lookupPostcode }} from "../../api/postcodeApi";
import type {{ QuoteFormProps }} from "../forms";

/** {name} ({code}) quote form. Sold in: {region}. Maximum cover {maxcover:,}. */
const VOLUNTARY_EXCESS = {volx};

export function validate{code}(a: Record<string, unknown>): string[] {{
  const e: string[] = [];
{''.join(ts_check(n, t, r) for n, t, _l, r in fields)}  return e;
}}

export function {comp}({{ onSubmit }}: QuoteFormProps) {{
  const [a, setA] = useState<Record<string, unknown>>({{}});
  const [postcode, setPostcode] = useState("");
  const [voluntaryExcess, setVx] = useState({volx[0]});
  const [errors, setErrors] = useState<string[]>([]);
  const set = (k: string, v: unknown) => setA((s) => ({{ ...s, [k]: v }}));
  async function submit() {{
    const e = validate{code}(a);
    if (!(await lookupPostcode(postcode)).length) e.push("We could not find that postcode");
    setErrors(e);
    if (!e.length) onSubmit({{ line: "{code}", postcode, voluntaryExcess, answers: a }});
  }}
  return (
    <form onSubmit={{(ev) => {{ ev.preventDefault(); submit(); }}}}>
      <h1>{name} insurance quote</h1>
{''.join(ts_input(n, t, l) for n, t, l, _r in fields)}      <label>Postcode <input onChange={{(ev) => setPostcode(ev.target.value)}} /></label>
      <label>Voluntary excess <select onChange={{(ev) => setVx(Number(ev.target.value))}}>{{VOLUNTARY_EXCESS.map((v) => <option key={{v}}>{{v}}</option>)}}</select></label>
      {{errors.map((m) => <p role="alert" key={{m}}>{{m}}</p>)}}
      <button type="submit">Get my price</button>
    </form>
  );
}}
""")
    W(f"docs/product/lines/{code}-{name.lower().replace(' ', '-')}.md", f"""
# {name} ({code}): product guide

**Sold in:** {region.replace('+', ' and ')}. **Maximum cover:** {maxcover:,}. **Voluntary excess options:** {', '.join(map(str, volx))}.

## What we ask at quote

| Question | Why we ask |
|---|---|
""" + "".join(f"| {l} | {rng.choice(['Main rating factor', 'Underwriting acceptance', 'Fraud prevention', 'Sets the sum insured', 'Loading or discount'])} |\n" for _n, _t, l, _r in fields) + f"""
Quotes are referred to an underwriter when *{referral}* is outside appetite.

## Not covered

""" + "".join(f"- {x}\n" for x in excl) + """
## Optional extras

""" + "".join(f"- {x}\n" for x in extras) + f"""
## Claims

Report a claim online through the five-step claim form, or by phone. {name} claims are handled by the
{rng.choice(['personal lines', 'commercial lines', 'specialty'])} claims team.
""")

# minified bundle in dist (generated output, scope trap)
ids = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p"]
parts = ['/*! customer-portal 3.8.2 | build 2026-11-03 */', '(function(){"use strict";']
for code, name, comp, region, fields, *_ in LINES:
    v = rng.sample(ids, 3)
    checks = ",".join(f'"{n}"' for n, *_ in fields)
    parts.append(f'var {comp}=function({v[0]}){{var {v[1]}=[{checks}],{v[2]}=[];return {v[1]}.forEach(function(x){{{v[0]}[x]===void 0&&{v[2]}.push(x+" is required")}}),{v[2]}}};')
parts.append('var F=["PolicyLookup","IncidentDetails","DamageAndPhotos","Review","Submit"];'
             'function R(t,p,o){return fetch(p,Object.assign({headers:{"Content-Type":"application/json",Authorization:"Bearer "+t}},o)).then(function(r){if(!r.ok)throw new Error("API "+r.status);return r.json()})}'
             'var C={draft:function(t,n){return R(t,"/api/claims/v1/claims/drafts",{method:"POST",body:JSON.stringify({policyNumber:n})})},'
             'register:function(t,d,i){return R(t,"/api/claims/v1/claims",{method:"POST",body:JSON.stringify(Object.assign({draftId:d},i))})}};'
             'var P={get:function(t,n){return R(t,"/api/policies/v1/policies/"+encodeURIComponent(n))},quote:function(t,q){return R(t,"/api/policies/v1/quotes",{method:"POST",body:JSON.stringify(q)})}};'
             'window.__CORVANE__={steps:F,claims:C,policies:P};})();')
W("web/customer-portal/dist/assets/index-3f9a1c.min.js", "".join(parts) + "\n")
W("web/customer-portal/dist/index.html", '<!doctype html><html lang="en"><head><meta charset="UTF-8"><title>Corvane Mutual</title>'
  '<script type="module" crossorigin src="/assets/index-3f9a1c.min.js"></script></head><body><div id="root"></div></body></html>\n')
print("bulk written")
