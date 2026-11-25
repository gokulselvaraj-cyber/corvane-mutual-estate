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
