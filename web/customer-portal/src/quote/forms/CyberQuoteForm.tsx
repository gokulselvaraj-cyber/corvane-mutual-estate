import { useState } from "react";
import { lookupPostcode } from "../../api/postcodeApi";
import type { QuoteFormProps } from "../forms";

/** Cyber (CYB) quote form. Sold in: UK+US. Maximum cover 10,000,000. */
const VOLUNTARY_EXCESS = [0, 250, 750, 1000];

export function validateCYB(a: Record<string, unknown>): string[] {
  const e: string[] = [];
  if (!(Number(a.annualRevenue) >= 100000 && Number(a.annualRevenue) <= 250000000)) e.push("annualRevenue must be between 100000 and 250000000");
  if (!(Number(a.recordsHeld) >= 0 && Number(a.recordsHeld) <= 50000000)) e.push("recordsHeld must be between 0 and 50000000");
  if (a.mfaEnforced !== true) e.push("We can only quote when mfaEnforced is in place");
  return e;
}

export function CyberQuoteForm({ onSubmit }: QuoteFormProps) {
  const [a, setA] = useState<Record<string, unknown>>({});
  const [postcode, setPostcode] = useState("");
  const [voluntaryExcess, setVx] = useState(0);
  const [errors, setErrors] = useState<string[]>([]);
  const set = (k: string, v: unknown) => setA((s) => ({ ...s, [k]: v }));
  async function submit() {
    const e = validateCYB(a);
    if (!(await lookupPostcode(postcode)).length) e.push("We could not find that postcode");
    setErrors(e);
    if (!e.length) onSubmit({ line: "CYB", postcode, voluntaryExcess, answers: a });
  }
  return (
    <form onSubmit={(ev) => { ev.preventDefault(); submit(); }}>
      <h1>Cyber insurance quote</h1>
      <label>Annual revenue <input type="number" onChange={(ev) => set("annualRevenue", Number(ev.target.value))} /></label>
      <label>Personal data records held <input type="number" onChange={(ev) => set("recordsHeld", Number(ev.target.value))} /></label>
      <label><input type="checkbox" onChange={(ev) => set("mfaEnforced", ev.target.checked)} /> Is MFA enforced for all remote access?</label>
      <label><input type="checkbox" onChange={(ev) => set("offlineBackups", ev.target.checked)} /> Are backups kept offline?</label>
      <label>Postcode <input onChange={(ev) => setPostcode(ev.target.value)} /></label>
      <label>Voluntary excess <select onChange={(ev) => setVx(Number(ev.target.value))}>{VOLUNTARY_EXCESS.map((v) => <option key={v}>{v}</option>)}</select></label>
      {errors.map((m) => <p role="alert" key={m}>{m}</p>)}
      <button type="submit">Get my price</button>
    </form>
  );
}
