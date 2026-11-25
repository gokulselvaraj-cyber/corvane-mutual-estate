import type { LineCode } from "../model/Policy";

export const LINES: { code: LineCode; name: string; region: string }[] = [
  { code: "MTR", name: "Motor", region: "UK+US" },
  { code: "HOM", name: "Home buildings", region: "UK" },
  { code: "CNT", name: "Home contents", region: "UK" },
  { code: "TRV", name: "Travel", region: "UK+US" },
  { code: "PET", name: "Pet", region: "UK" },
  { code: "LLD", name: "Landlord", region: "UK" },
  { code: "MAR", name: "Marine cargo", region: "UK+US" },
  { code: "CPR", name: "Commercial property", region: "UK+US" },
  { code: "PLB", name: "Public liability", region: "UK+US" },
  { code: "PIN", name: "Professional indemnity", region: "UK+US" },
  { code: "CYB", name: "Cyber", region: "UK+US" },
  { code: "GDG", name: "Gadget", region: "UK" },
];
