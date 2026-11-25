const NAMES: Record<string, string> = {
  MTR: "Motor", HOM: "Home buildings", CNT: "Home contents", TRV: "Travel", PET: "Pet", LLD: "Landlord",
  MAR: "Marine cargo", CPR: "Commercial property", PLB: "Public liability", PIN: "Professional indemnity",
  CYB: "Cyber", GDG: "Gadget",
};
export const lineName = (code: string): string => NAMES[code] ?? code;
