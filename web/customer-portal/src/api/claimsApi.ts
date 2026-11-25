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
