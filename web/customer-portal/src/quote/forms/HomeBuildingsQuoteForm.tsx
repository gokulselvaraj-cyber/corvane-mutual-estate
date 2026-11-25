import { useState } from "react";
import { lookupPostcode } from "../../api/postcodeApi";
import type { QuoteFormProps } from "../forms";

/** Home buildings (HOM) quote form. Sold in: UK. Maximum cover 2,500,000. */
const VOLUNTARY_EXCESS = [0, 250, 300, 750];

export function validateHOM(a: Record<string, unknown>): string[] {
  const e: string[] = [];
  if (!(Number(a.rebuildCost) >= 50000 && Number(a.rebuildCost) <= 2500000)) e.push("rebuildCost must be between 50000 and 2500000");
  if (!(Number(a.yearBuilt) >= 1600 && Number(a.yearBuilt) <= 2026)) e.push("yearBuilt must be between 1600 and 2026");
  if (a.roofType === undefined || a.roofType === "") e.push("roofType is required");
  return e;
}

export function HomeBuildingsQuoteForm({ onSubmit }: QuoteFormProps) {
  const [a, setA] = useState<Record<string, unknown>>({});
  const [postcode, setPostcode] = useState("");
  const [voluntaryExcess, setVx] = useState(0);
  const [errors, setErrors] = useState<string[]>([]);
  const set = (k: string, v: unknown) => setA((s) => ({ ...s, [k]: v }));
  async function submit() {
    const e = validateHOM(a);
    if (!(await lookupPostcode(postcode)).length) e.push("We could not find that postcode");
    setErrors(e);
    if (!e.length) onSubmit({ line: "HOM", postcode, voluntaryExcess, answers: a });
  }
  return (
    <form onSubmit={(ev) => { ev.preventDefault(); submit(); }}>
      <h1>Home buildings insurance quote</h1>
      <label>Rebuild cost <input type="number" onChange={(ev) => set("rebuildCost", Number(ev.target.value))} /></label>
      <label>Year built <input type="number" onChange={(ev) => set("yearBuilt", Number(ev.target.value))} /></label>
      <label>Roof type <select onChange={(ev) => set("roofType", ev.target.value)}><option value="" /><option>STANDARD</option><option>FLAT</option><option>THATCH</option></select></label>
      <label><input type="checkbox" onChange={(ev) => set("listedBuilding", ev.target.checked)} /> Is it a listed building?</label>
      <label><input type="checkbox" onChange={(ev) => set("floodHistory", ev.target.checked)} /> Has the property flooded in the last 10 years?</label>
      <label>Postcode <input onChange={(ev) => setPostcode(ev.target.value)} /></label>
      <label>Voluntary excess <select onChange={(ev) => setVx(Number(ev.target.value))}>{VOLUNTARY_EXCESS.map((v) => <option key={v}>{v}</option>)}</select></label>
      {errors.map((m) => <p role="alert" key={m}>{m}</p>)}
      <button type="submit">Get my price</button>
    </form>
  );
}
