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
