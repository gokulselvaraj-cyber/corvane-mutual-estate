import { useState } from "react";
import { lookupPostcode } from "../../api/postcodeApi";
import type { QuoteFormProps } from "../forms";

/** Commercial property (CPR) quote form. Sold in: UK+US. Maximum cover 50,000,000. */
const VOLUNTARY_EXCESS = [200, 400, 500, 1000];

export function validateCPR(a: Record<string, unknown>): string[] {
  const e: string[] = [];
  if (a.occupancy === undefined || a.occupancy === "") e.push("occupancy is required");
  if (!(Number(a.buildingSumInsured) >= 100000 && Number(a.buildingSumInsured) <= 50000000)) e.push("buildingSumInsured must be between 100000 and 50000000");
  if (!(Number(a.businessInterruptionMonths) >= 0 && Number(a.businessInterruptionMonths) <= 36)) e.push("businessInterruptionMonths must be between 0 and 36");
  return e;
}

export function CommercialPropertyQuoteForm({ onSubmit }: QuoteFormProps) {
  const [a, setA] = useState<Record<string, unknown>>({});
  const [postcode, setPostcode] = useState("");
  const [voluntaryExcess, setVx] = useState(200);
  const [errors, setErrors] = useState<string[]>([]);
  const set = (k: string, v: unknown) => setA((s) => ({ ...s, [k]: v }));
  async function submit() {
    const e = validateCPR(a);
    if (!(await lookupPostcode(postcode)).length) e.push("We could not find that postcode");
    setErrors(e);
    if (!e.length) onSubmit({ line: "CPR", postcode, voluntaryExcess, answers: a });
  }
  return (
    <form onSubmit={(ev) => { ev.preventDefault(); submit(); }}>
      <h1>Commercial property insurance quote</h1>
      <label>Occupancy <select onChange={(ev) => set("occupancy", ev.target.value)}><option value="" /><option>OFFICE</option><option>RETAIL</option><option>WAREHOUSE</option><option>LIGHT_INDUSTRIAL</option></select></label>
      <label>Buildings sum insured <input type="number" onChange={(ev) => set("buildingSumInsured", Number(ev.target.value))} /></label>
      <label><input type="checkbox" onChange={(ev) => set("sprinklers", ev.target.checked)} /> Sprinklers fitted?</label>
      <label>Business interruption period (months) <input type="number" onChange={(ev) => set("businessInterruptionMonths", Number(ev.target.value))} /></label>
      <label>Postcode <input onChange={(ev) => setPostcode(ev.target.value)} /></label>
      <label>Voluntary excess <select onChange={(ev) => setVx(Number(ev.target.value))}>{VOLUNTARY_EXCESS.map((v) => <option key={v}>{v}</option>)}</select></label>
      {errors.map((m) => <p role="alert" key={m}>{m}</p>)}
      <button type="submit">Get my price</button>
    </form>
  );
}
