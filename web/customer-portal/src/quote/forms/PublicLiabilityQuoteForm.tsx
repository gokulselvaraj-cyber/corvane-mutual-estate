import { useState } from "react";
import { lookupPostcode } from "../../api/postcodeApi";
import type { QuoteFormProps } from "../forms";

/** Public liability (PLB) quote form. Sold in: UK+US. Maximum cover 10,000,000. */
const VOLUNTARY_EXCESS = [0, 150, 200, 750];

export function validatePLB(a: Record<string, unknown>): string[] {
  const e: string[] = [];
  if (a.trade === undefined || a.trade === "") e.push("trade is required");
  if (!(Number(a.annualTurnover) >= 10000 && Number(a.annualTurnover) <= 20000000)) e.push("annualTurnover must be between 10000 and 20000000");
  if (!(Number(a.employees) >= 0 && Number(a.employees) <= 500)) e.push("employees must be between 0 and 500");
  if (a.limitOfIndemnity === undefined || a.limitOfIndemnity === "") e.push("limitOfIndemnity is required");
  return e;
}

export function PublicLiabilityQuoteForm({ onSubmit }: QuoteFormProps) {
  const [a, setA] = useState<Record<string, unknown>>({});
  const [postcode, setPostcode] = useState("");
  const [voluntaryExcess, setVx] = useState(0);
  const [errors, setErrors] = useState<string[]>([]);
  const set = (k: string, v: unknown) => setA((s) => ({ ...s, [k]: v }));
  async function submit() {
    const e = validatePLB(a);
    if (!(await lookupPostcode(postcode)).length) e.push("We could not find that postcode");
    setErrors(e);
    if (!e.length) onSubmit({ line: "PLB", postcode, voluntaryExcess, answers: a });
  }
  return (
    <form onSubmit={(ev) => { ev.preventDefault(); submit(); }}>
      <h1>Public liability insurance quote</h1>
      <label>Trade or business <input type="text" onChange={(ev) => set("trade", ev.target.value)} /></label>
      <label>Annual turnover <input type="number" onChange={(ev) => set("annualTurnover", Number(ev.target.value))} /></label>
      <label>Number of employees <input type="number" onChange={(ev) => set("employees", Number(ev.target.value))} /></label>
      <label>Limit of indemnity <select onChange={(ev) => set("limitOfIndemnity", ev.target.value)}><option value="" /><option>1000000</option><option>2000000</option><option>5000000</option><option>10000000</option></select></label>
      <label>Postcode <input onChange={(ev) => setPostcode(ev.target.value)} /></label>
      <label>Voluntary excess <select onChange={(ev) => setVx(Number(ev.target.value))}>{VOLUNTARY_EXCESS.map((v) => <option key={v}>{v}</option>)}</select></label>
      {errors.map((m) => <p role="alert" key={m}>{m}</p>)}
      <button type="submit">Get my price</button>
    </form>
  );
}
