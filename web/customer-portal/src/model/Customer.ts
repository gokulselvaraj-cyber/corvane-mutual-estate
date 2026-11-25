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
