"""Builder E: writes web/customer-portal (hand-written core). Run: python3 -I e_portal.py <estate_root>"""
import os, sys

ROOT = sys.argv[1]


def W(path, text):
    p = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text.lstrip("\n"))


P = "web/customer-portal/"

W(P + "package.json", """
{
  "name": "@corvane/customer-portal",
  "version": "3.8.2",
  "private": true,
  "description": "Corvane Mutual customer portal: quotes, policy view and first notice of loss (FNOL)",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "test": "vitest run",
    "lint": "eslint src --ext .ts,.tsx"
  },
  "dependencies": {
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "react-router-dom": "6.26.2",
    "@corvane/policy-client": "file:../../generated/policy-client-ts",
    "zod": "3.23.8"
  },
  "devDependencies": {
    "@testing-library/react": "16.0.1",
    "@types/react": "18.3.5",
    "@vitejs/plugin-react": "4.3.1",
    "typescript": "5.5.4",
    "vite": "5.4.6",
    "vitest": "2.1.1",
    "eslint": "8.57.0"
  }
}
""")

W(P + "tsconfig.json", """
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noEmit": true,
    "lib": ["ES2022", "DOM"],
    "types": ["vitest/globals"]
  },
  "include": ["src"]
}
""")

W(P + "Dockerfile", """
# Customer portal: built with Vite, served by nginx on 8080 (non-root)
FROM node:20.17-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install --no-audit --no-fund
COPY . .
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
HEALTHCHECK CMD wget -qO- http://localhost:8080/healthz || exit 1
""")

W(P + "nginx.conf", """
server {
  listen 8080;
  root /usr/share/nginx/html;
  location /healthz { return 200 'ok'; }
  # API calls go through the edge gateway; the portal never talks to services directly in prod.
  location /api/claims/   { proxy_pass http://claims-service:8080/;  proxy_read_timeout 15s; }
  location /api/policies/ { proxy_pass http://policy-admin:8080/;    proxy_read_timeout 15s; }
  location / { try_files $uri /index.html; }
}
""")

W(P + "README.md", """
# Customer portal

React 18 + TypeScript single-page app for Corvane Mutual customers.

| Area | Route | Backend |
|---|---|---|
| Get a quote | `/quote/:line` | policy-admin `POST /v1/quotes` |
| View my policy | `/policies/:policyNumber` | policy-admin `GET /v1/policies/{policyNumber}` |
| Report a claim (FNOL) | `/claims/new` | claims-service `POST /v1/claims/drafts`, `POST /v1/claims/drafts/{id}/photos`, `POST /v1/claims` |

The FNOL wizard has five steps: PolicyLookup, IncidentDetails, DamageAndPhotos, Review, Submit.

Postcode lookup uses `https://postcode.lookup.example/v1` (external).

Owned by the Digital team (`@corvane/digital`). Built and deployed by `.github/workflows/portal.yml`.

`dist/` holds the last production bundle checked in for the CDN cache-warm job. It is generated output; do not edit.
""")

W(P + "catalog-info.yaml", """
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: customer-portal
  description: Customer-facing web portal (quotes, policy view, FNOL)
  annotations:
    github.com/project-slug: corvane/customer-portal
spec:
  type: website
  lifecycle: production
  owner: team-digital
  system: corvane-insurance-platform
  consumesApis:
    - claims-api
    - policy-admin-api
    - postcode-lookup-api
""")

W(P + "src/main.tsx", """
import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { App } from "./App";
import { AuthProvider } from "./auth/AuthProvider";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AuthProvider issuer="https://login.corvane.internal" clientId="customer-portal">
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </AuthProvider>
  </React.StrictMode>,
);
""")

W(P + "src/App.tsx", """
import { Routes, Route, Navigate } from "react-router-dom";
import { QuotePage } from "./pages/QuotePage";
import { PolicyView } from "./pages/PolicyView";
import { FnolWizard } from "./fnol/FnolWizard";
import { RequireRole } from "./auth/RequireRole";
import { Home } from "./pages/Home";

/** Route table. Every route except Home and quotes needs the CUSTOMER role from the Corvane identity provider. */
export function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/quote/:line" element={<QuotePage />} />
      <Route path="/policies/:policyNumber" element={<RequireRole role="CUSTOMER"><PolicyView /></RequireRole>} />
      <Route path="/claims/new" element={<RequireRole role="CUSTOMER"><FnolWizard /></RequireRole>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
""")

W(P + "src/auth/AuthProvider.tsx", """
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export interface Session { token: string; roles: string[]; customerId: string }
const Ctx = createContext<Session | null>(null);

/** OIDC login against the Corvane identity provider. The access token lives in memory only, never in localStorage. */
export function AuthProvider({ issuer, clientId, children }: { issuer: string; clientId: string; children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  useEffect(() => {
    fetch(`${issuer}/session?client_id=${clientId}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((s) => s && setSession({ token: s.access_token, roles: s.roles ?? [], customerId: s.sub }));
  }, [issuer, clientId]);
  return <Ctx.Provider value={session}>{children}</Ctx.Provider>;
}

export const useSession = () => useContext(Ctx);
""")

W(P + "src/auth/RequireRole.tsx", """
import type { ReactNode } from "react";
import { useSession } from "./AuthProvider";

export function RequireRole({ role, children }: { role: "CUSTOMER" | "BROKER"; children: ReactNode }) {
  const s = useSession();
  if (!s) return <p>Signing you in…</p>;
  if (!s.roles.includes(role)) return <p role="alert">You do not have access to this page.</p>;
  return <>{children}</>;
}
""")

W(P + "src/model/Customer.ts", """
/**
 * The person who holds a policy, as the portal sees them.
 * The same person is PolicyHolder in policy-admin, INSURED in the mainframe POLREC copybook,
 * PARTY in the Oracle ledger and claim_party (role 'policyholder') in the claims database.
 */
export interface Customer {
  customerId: string;
  title?: "Mr" | "Mrs" | "Ms" | "Mx" | "Dr";
  firstName: string;
  lastName: string;
  dateOfBirth: string; // ISO date; personal data
  email: string;
  phone?: string;
  address: Address;
  /** UK National Insurance number or US SSN. Never shown in full: masked to the last 3 characters. */
  nationalIdMasked?: string;
  region: "UK" | "US";
}

export interface Address {
  line1: string;
  line2?: string;
  town: string;
  postcode: string;
  country: "GB" | "US";
}

export const fullName = (c: Customer) => `${c.firstName} ${c.lastName}`;
""")

W(P + "src/model/Policy.ts", """
import type { Customer } from "./Customer";

export type LineCode = "MTR" | "HOM" | "CNT" | "TRV" | "PET" | "LLD" | "MAR" | "CPR" | "PLB" | "PIN" | "CYB" | "GDG";

export interface PolicySummary {
  policyNumber: string; // e.g. CVM-MTR-0012345
  line: LineCode;
  status: "QUOTED" | "BOUND" | "LAPSED" | "CANCELLED";
  inceptionDate: string;
  expiryDate: string;
  annualPremium: number; // GBP or USD, includes insurance premium tax (IPT)
  currency: "GBP" | "USD";
  compulsoryExcess: number;
  voluntaryExcess: number;
  holder: Customer;
}
""")

W(P + "src/api/http.ts", """
import { useSession } from "../auth/AuthProvider";

export class ApiError extends Error {
  constructor(public status: number, public body: string) { super(`API ${status}`); }
}

const TIMEOUT_MS = 15000;

/** All calls go through the edge path /api/...; nginx forwards to the services. */
export async function call<T>(token: string | undefined, path: string, init: RequestInit = {}): Promise<T> {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(path, {
      ...init,
      signal: ctl.signal,
      headers: { ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
                 ...(token ? { Authorization: `Bearer ${token}` } : {}), ...init.headers },
    });
    if (!res.ok) throw new ApiError(res.status, await res.text());
    return (await res.json()) as T;
  } finally {
    clearTimeout(t);
  }
}

export const useToken = () => useSession()?.token;
""")

W(P + "src/api/claimsApi.ts", """
import { call } from "./http";

/** claims-service endpoints used by the FNOL wizard (see contracts/claims.openapi.yaml). */
export interface ClaimDraft { draftId: string; policyNumber: string }
export interface IncidentDetails {
  lossDate: string;
  lossCause: string;
  description: string;
  injuryInvolved: boolean;
  injuryNotes?: string; // personal health data: only sent when injuryInvolved
  estimatedAmount: number;
  thirdPartyInvolved: boolean;
}
export interface RegisteredClaim { claimId: string; status: "REGISTERED" | "AUTO_APPROVED" | "REFERRED"; reference: string }

const BASE = "/api/claims/v1/claims";

export const createDraft = (token: string | undefined, policyNumber: string) =>
  call<ClaimDraft>(token, `${BASE}/drafts`, { method: "POST", body: JSON.stringify({ policyNumber }) });

export function uploadPhoto(token: string | undefined, draftId: string, file: File) {
  const form = new FormData();
  form.append("photo", file);
  return call<{ photoId: string }>(token, `${BASE}/drafts/${draftId}/photos`, { method: "POST", body: form });
}

export const registerClaim = (token: string | undefined, draftId: string, incident: IncidentDetails) =>
  call<RegisteredClaim>(token, BASE, { method: "POST", body: JSON.stringify({ draftId, ...incident }) });

export const claimSummary = (token: string | undefined, claimId: string) =>
  call<{ claimId: string; status: string; paidAmount?: number }>(token, `${BASE}/${claimId}/summary`);
""")

W(P + "src/api/policyApi.ts", """
import { call } from "./http";
import type { LineCode, PolicySummary } from "../model/Policy";

/**
 * policy-admin calls. The generated client in generated/policy-client-ts covers the same API, but the portal
 * still uses these hand-written wrappers (migration to the generated client is half done: see ADR-0010).
 */
const BASE = "/api/policies/v1";

export const getPolicy = (token: string | undefined, policyNumber: string) =>
  call<PolicySummary>(token, `${BASE}/policies/${encodeURIComponent(policyNumber)}`);

export interface QuoteRequest { line: LineCode; postcode: string; voluntaryExcess: number; answers: Record<string, unknown> }
export interface QuoteResponse { quoteId: string; annualPremium: number; ipt: number; currency: "GBP" | "USD"; referred: boolean }

export const requestQuote = (token: string | undefined, req: QuoteRequest) =>
  call<QuoteResponse>(token, `${BASE}/quotes`, { method: "POST", body: JSON.stringify(req) });

export const bindQuote = (token: string | undefined, quoteId: string) =>
  call<PolicySummary>(token, `${BASE}/policies/${quoteId}/bind`, { method: "POST" });
""")

W(P + "src/api/postcodeApi.ts", """
/** External postcode lookup (outside the Corvane boundary). Called straight from the browser. */
const POSTCODE_API = "https://postcode.lookup.example/v1";

export interface PostcodeHit { postcode: string; town: string; lines: string[] }

export async function lookupPostcode(postcode: string): Promise<PostcodeHit[]> {
  const res = await fetch(`${POSTCODE_API}/addresses?postcode=${encodeURIComponent(postcode.trim())}`);
  if (!res.ok) return [];
  return (await res.json()).results as PostcodeHit[];
}
""")

W(P + "src/fnol/FnolWizard.tsx", """
import { useState } from "react";
import { PolicyLookup } from "./steps/PolicyLookup";
import { IncidentDetailsStep } from "./steps/IncidentDetails";
import { DamageAndPhotos } from "./steps/DamageAndPhotos";
import { Review } from "./steps/Review";
import { Submit } from "./steps/Submit";
import type { IncidentDetails } from "../api/claimsApi";

/** First notice of loss: the five steps, in order. Journey J1 starts here. */
export const STEPS = ["PolicyLookup", "IncidentDetails", "DamageAndPhotos", "Review", "Submit"] as const;
export type Step = (typeof STEPS)[number];

export interface FnolState {
  policyNumber?: string;
  draftId?: string;
  incident?: IncidentDetails;
  photos: File[];
}

export function FnolWizard() {
  const [step, setStep] = useState<Step>("PolicyLookup");
  const [state, setState] = useState<FnolState>({ photos: [] });
  const next = () => setStep(STEPS[Math.min(STEPS.indexOf(step) + 1, STEPS.length - 1)]);
  const back = () => setStep(STEPS[Math.max(STEPS.indexOf(step) - 1, 0)]);
  const update = (p: Partial<FnolState>) => setState((s) => ({ ...s, ...p }));

  return (
    <main aria-label="Report a claim">
      <ol className="steps">{STEPS.map((s) => <li key={s} aria-current={s === step}>{s}</li>)}</ol>
      {step === "PolicyLookup" && <PolicyLookup state={state} update={update} next={next} />}
      {step === "IncidentDetails" && <IncidentDetailsStep state={state} update={update} next={next} back={back} />}
      {step === "DamageAndPhotos" && <DamageAndPhotos state={state} update={update} next={next} back={back} />}
      {step === "Review" && <Review state={state} next={next} back={back} />}
      {step === "Submit" && <Submit state={state} />}
    </main>
  );
}
""")

W(P + "src/fnol/steps/PolicyLookup.tsx", """
import { useState } from "react";
import { getPolicy } from "../../api/policyApi";
import { createDraft } from "../../api/claimsApi";
import { useToken } from "../../api/http";
import type { FnolState } from "../FnolWizard";

const POLICY_NUMBER = /^CVM-(MTR|HOM|CNT|TRV|PET|LLD|MAR|CPR|PLB|PIN|CYB|GDG)-\\d{7}$/;

export function PolicyLookup({ update, next }: { state: FnolState; update: (p: Partial<FnolState>) => void; next: () => void }) {
  const token = useToken();
  const [value, setValue] = useState("");
  const [error, setError] = useState<string>();
  async function find() {
    if (!POLICY_NUMBER.test(value)) return setError("Policy numbers look like CVM-MTR-0012345.");
    const policy = await getPolicy(token, value);
    if (policy.status !== "BOUND") return setError("This policy is not active, so a claim cannot be reported online.");
    const draft = await createDraft(token, value);
    update({ policyNumber: value, draftId: draft.draftId });
    next();
  }
  return (
    <section>
      <label>Policy number <input value={value} onChange={(e) => setValue(e.target.value.toUpperCase())} /></label>
      {error && <p role="alert">{error}</p>}
      <button onClick={find}>Find my policy</button>
    </section>
  );
}
""")

W(P + "src/fnol/steps/IncidentDetails.tsx", """
import { useState } from "react";
import type { IncidentDetails } from "../../api/claimsApi";
import type { FnolState } from "../FnolWizard";

/** Loss date may not be in the future or more than 180 days ago (claims-service enforces per-line windows too). */
export function validateIncident(i: IncidentDetails, today = new Date()): string[] {
  const errors: string[] = [];
  const loss = new Date(i.lossDate);
  if (loss > today) errors.push("The loss date cannot be in the future.");
  if ((today.getTime() - loss.getTime()) / 86400000 > 180) errors.push("Losses older than 180 days must be reported by phone.");
  if (i.description.trim().length < 20) errors.push("Please describe what happened in at least 20 characters.");
  if (i.injuryInvolved && !i.injuryNotes) errors.push("Please tell us about the injury.");
  if (i.estimatedAmount <= 0) errors.push("Enter an estimated amount.");
  return errors;
}

export function IncidentDetailsStep({ update, next, back }: { state: FnolState; update: (p: Partial<FnolState>) => void; next: () => void; back: () => void }) {
  const [i, setI] = useState<IncidentDetails>({ lossDate: "", lossCause: "", description: "", injuryInvolved: false, estimatedAmount: 0, thirdPartyInvolved: false });
  const [errors, setErrors] = useState<string[]>([]);
  const go = () => { const e = validateIncident(i); setErrors(e); if (!e.length) { update({ incident: i }); next(); } };
  return (
    <section>
      <input type="date" aria-label="Loss date" onChange={(e) => setI({ ...i, lossDate: e.target.value })} />
      <textarea aria-label="What happened" onChange={(e) => setI({ ...i, description: e.target.value })} />
      <label><input type="checkbox" onChange={(e) => setI({ ...i, injuryInvolved: e.target.checked })} /> Someone was injured</label>
      {i.injuryInvolved && <textarea aria-label="Injury details" onChange={(e) => setI({ ...i, injuryNotes: e.target.value })} />}
      <input type="number" aria-label="Estimated amount" onChange={(e) => setI({ ...i, estimatedAmount: Number(e.target.value) })} />
      {errors.map((e) => <p role="alert" key={e}>{e}</p>)}
      <button onClick={back}>Back</button><button onClick={go}>Continue</button>
    </section>
  );
}
""")

W(P + "src/fnol/steps/DamageAndPhotos.tsx", """
import { uploadPhoto } from "../../api/claimsApi";
import { useToken } from "../../api/http";
import type { FnolState } from "../FnolWizard";

const MAX_PHOTOS = 8;
const MAX_BYTES = 10 * 1024 * 1024;

export function DamageAndPhotos({ state, update, next, back }: { state: FnolState; update: (p: Partial<FnolState>) => void; next: () => void; back: () => void }) {
  const token = useToken();
  async function add(files: FileList | null) {
    const ok = Array.from(files ?? []).filter((f) => f.size <= MAX_BYTES).slice(0, MAX_PHOTOS - state.photos.length);
    for (const f of ok) await uploadPhoto(token, state.draftId!, f);
    update({ photos: [...state.photos, ...ok] });
  }
  return (
    <section>
      <input type="file" accept="image/*" multiple onChange={(e) => add(e.target.files)} />
      <p>{state.photos.length} of {MAX_PHOTOS} photos added</p>
      <button onClick={back}>Back</button><button onClick={next}>Continue</button>
    </section>
  );
}
""")

W(P + "src/fnol/steps/Review.tsx", """
import type { FnolState } from "../FnolWizard";

export function Review({ state, next, back }: { state: FnolState; next: () => void; back: () => void }) {
  const i = state.incident!;
  return (
    <section>
      <h2>Check your claim</h2>
      <dl>
        <dt>Policy</dt><dd>{state.policyNumber}</dd>
        <dt>Loss date</dt><dd>{i.lossDate}</dd>
        <dt>Estimated amount</dt><dd>{i.estimatedAmount}</dd>
        <dt>Photos</dt><dd>{state.photos.length}</dd>
      </dl>
      <p>Claims under our auto-approval limit may be settled without an adjuster.</p>
      <button onClick={back}>Back</button><button onClick={next}>Submit claim</button>
    </section>
  );
}
""")

W(P + "src/fnol/steps/Submit.tsx", """
import { useEffect, useState } from "react";
import { registerClaim, type RegisteredClaim } from "../../api/claimsApi";
import { useToken } from "../../api/http";
import type { FnolState } from "../FnolWizard";

export function Submit({ state }: { state: FnolState }) {
  const token = useToken();
  const [result, setResult] = useState<RegisteredClaim>();
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    registerClaim(token, state.draftId!, state.incident!).then(setResult, () => setFailed(true));
  }, [token, state]);
  if (failed) return <p role="alert">We could not submit your claim. Please call 0800 000 0000.</p>;
  if (!result) return <p>Submitting…</p>;
  return (
    <section>
      <h2>Claim {result.reference} received</h2>
      {result.status === "AUTO_APPROVED" && <p>Good news: your claim has been approved. Payment usually arrives within 3 working days.</p>}
      {result.status === "REFERRED" && <p>An adjuster will contact you within 2 working days.</p>}
      {result.status === "REGISTERED" && <p>We are reviewing your claim.</p>}
    </section>
  );
}
""")

W(P + "src/pages/Home.tsx", """
import { Link } from "react-router-dom";
import { LINES } from "../quote/lines";

export function Home() {
  return (
    <main>
      <h1>Corvane Mutual</h1>
      <ul>{LINES.map((l) => <li key={l.code}><Link to={`/quote/${l.code}`}>{l.name} insurance</Link></li>)}</ul>
      <Link to="/claims/new">Report a claim</Link>
    </main>
  );
}
""")

W(P + "src/pages/QuotePage.tsx", """
import { useParams } from "react-router-dom";
import { useState } from "react";
import { requestQuote, bindQuote, type QuoteResponse } from "../api/policyApi";
import { useToken } from "../api/http";
import { FORMS } from "../quote/forms";
import type { LineCode } from "../model/Policy";

/** Journey J4 starts here: quote, then bind. */
export function QuotePage() {
  const { line } = useParams<{ line: LineCode }>();
  const token = useToken();
  const [quote, setQuote] = useState<QuoteResponse>();
  const Form = FORMS[line!];
  if (!Form) return <p>Unknown product.</p>;
  return (
    <main>
      <Form onSubmit={async (req) => setQuote(await requestQuote(token, req))} />
      {quote && (
        <aside>
          <p>Annual premium {quote.currency} {quote.annualPremium.toFixed(2)} (includes IPT {quote.ipt.toFixed(2)})</p>
          {quote.referred ? <p>We need to check a few details before we can offer cover.</p>
            : <button onClick={() => bindQuote(token, quote.quoteId)}>Buy this policy</button>}
        </aside>
      )}
    </main>
  );
}
""")

W(P + "src/pages/PolicyView.tsx", """
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getPolicy } from "../api/policyApi";
import { useToken } from "../api/http";
import { fullName } from "../model/Customer";
import type { PolicySummary } from "../model/Policy";

export function PolicyView() {
  const { policyNumber } = useParams();
  const token = useToken();
  const [p, setP] = useState<PolicySummary>();
  useEffect(() => { getPolicy(token, policyNumber!).then(setP); }, [token, policyNumber]);
  if (!p) return <p>Loading…</p>;
  return (
    <main>
      <h1>{p.policyNumber}</h1>
      <p>Policyholder: {fullName(p.holder)}</p>
      <p>Cover from {p.inceptionDate} to {p.expiryDate}</p>
      <p>Excess: compulsory {p.compulsoryExcess} + voluntary {p.voluntaryExcess}</p>
      <p>Status: {p.status}</p>
    </main>
  );
}
""")

W(P + "src/fnol/IncidentDetails.test.tsx", """
import { validateIncident } from "./steps/IncidentDetails";

const base = { lossDate: "2026-11-01", lossCause: "THEFT", description: "Bike stolen from the locked garage overnight",
  injuryInvolved: false, estimatedAmount: 900, thirdPartyInvolved: false };
const today = new Date("2026-11-16");

describe("validateIncident", () => {
  it("accepts a normal claim", () => expect(validateIncident(base, today)).toEqual([]));
  it("rejects a future loss date", () =>
    expect(validateIncident({ ...base, lossDate: "2026-12-01" }, today)).toContain("The loss date cannot be in the future."));
  it("asks for injury details", () =>
    expect(validateIncident({ ...base, injuryInvolved: true }, today)).toContain("Please tell us about the injury."));
  it("sends old losses to the phone line", () =>
    expect(validateIncident({ ...base, lossDate: "2026-01-01" }, today)).toHaveLength(1));
});
""")

W(P + "src/fnol/FnolWizard.test.tsx", """
import { STEPS } from "./FnolWizard";

describe("FnolWizard", () => {
  it("has the five FNOL steps in order", () =>
    expect(STEPS).toEqual(["PolicyLookup", "IncidentDetails", "DamageAndPhotos", "Review", "Submit"]));
});
""")

W(P + "index.html", """
<!doctype html>
<html lang="en">
  <head><meta charset="UTF-8" /><title>Corvane Mutual</title></head>
  <body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body>
</html>
""")
print("portal core written")
