import { useState } from "react";
import { lookupPostcode } from "../../api/postcodeApi";
import type { QuoteFormProps } from "../forms";

/** Landlord (LLD) quote form. Sold in: UK. Maximum cover 2,000,000. */
const VOLUNTARY_EXCESS = [200, 300, 500, 1000];

export function validateLLD(a: Record<string, unknown>): string[] {
  const e: string[] = [];
  if (!(Number(a.propertiesCount) >= 1 && Number(a.propertiesCount) <= 20)) e.push("propertiesCount must be between 1 and 20");
  if (a.tenantType === undefined || a.tenantType === "") e.push("tenantType is required");
  if (!(Number(a.rentPerMonth) >= 200 && Number(a.rentPerMonth) <= 20000)) e.push("rentPerMonth must be between 200 and 20000");
  return e;
}

export function LandlordQuoteForm({ onSubmit }: QuoteFormProps) {
  const [a, setA] = useState<Record<string, unknown>>({});
  const [postcode, setPostcode] = useState("");
  const [voluntaryExcess, setVx] = useState(200);
  const [errors, setErrors] = useState<string[]>([]);
  const set = (k: string, v: unknown) => setA((s) => ({ ...s, [k]: v }));
  async function submit() {
    const e = validateLLD(a);
    if (!(await lookupPostcode(postcode)).length) e.push("We could not find that postcode");
    setErrors(e);
    if (!e.length) onSubmit({ line: "LLD", postcode, voluntaryExcess, answers: a });
  }
  return (
    <form onSubmit={(ev) => { ev.preventDefault(); submit(); }}>
      <h1>Landlord insurance quote</h1>
      <label>Number of let properties <input type="number" onChange={(ev) => set("propertiesCount", Number(ev.target.value))} /></label>
      <label>Tenant type <select onChange={(ev) => set("tenantType", ev.target.value)}><option value="" /><option>WORKING</option><option>STUDENT</option><option>DSS</option><option>HOLIDAY</option></select></label>
      <label>Rent per month <input type="number" onChange={(ev) => set("rentPerMonth", Number(ev.target.value))} /></label>
      <label><input type="checkbox" onChange={(ev) => set("hmo", ev.target.checked)} /> House in multiple occupation?</label>
      <label>Postcode <input onChange={(ev) => setPostcode(ev.target.value)} /></label>
      <label>Voluntary excess <select onChange={(ev) => setVx(Number(ev.target.value))}>{VOLUNTARY_EXCESS.map((v) => <option key={v}>{v}</option>)}</select></label>
      {errors.map((m) => <p role="alert" key={m}>{m}</p>)}
      <button type="submit">Get my price</button>
    </form>
  );
}
