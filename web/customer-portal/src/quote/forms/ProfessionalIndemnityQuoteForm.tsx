import { useState } from "react";
import { lookupPostcode } from "../../api/postcodeApi";
import type { QuoteFormProps } from "../forms";

/** Professional indemnity (PIN) quote form. Sold in: UK+US. Maximum cover 5,000,000. */
const VOLUNTARY_EXCESS = [0, 250, 400, 1000];

export function validatePIN(a: Record<string, unknown>): string[] {
  const e: string[] = [];
  if (a.profession === undefined || a.profession === "") e.push("profession is required");
  if (!(Number(a.feeIncome) >= 10000 && Number(a.feeIncome) <= 10000000)) e.push("feeIncome must be between 10000 and 10000000");
  if (!(Number(a.claimsLast5Years) >= 0 && Number(a.claimsLast5Years) <= 10)) e.push("claimsLast5Years must be between 0 and 10");
  if (a.limitOfIndemnity === undefined || a.limitOfIndemnity === "") e.push("limitOfIndemnity is required");
  return e;
}

export function ProfessionalIndemnityQuoteForm({ onSubmit }: QuoteFormProps) {
  const [a, setA] = useState<Record<string, unknown>>({});
  const [postcode, setPostcode] = useState("");
  const [voluntaryExcess, setVx] = useState(0);
  const [errors, setErrors] = useState<string[]>([]);
  const set = (k: string, v: unknown) => setA((s) => ({ ...s, [k]: v }));
  async function submit() {
    const e = validatePIN(a);
    if (!(await lookupPostcode(postcode)).length) e.push("We could not find that postcode");
    setErrors(e);
    if (!e.length) onSubmit({ line: "PIN", postcode, voluntaryExcess, answers: a });
  }
  return (
    <form onSubmit={(ev) => { ev.preventDefault(); submit(); }}>
      <h1>Professional indemnity insurance quote</h1>
      <label>Profession <select onChange={(ev) => set("profession", ev.target.value)}><option value="" /><option>ACCOUNTANT</option><option>ARCHITECT</option><option>CONSULTANT</option><option>IT_CONTRACTOR</option><option>SURVEYOR</option></select></label>
      <label>Annual fee income <input type="number" onChange={(ev) => set("feeIncome", Number(ev.target.value))} /></label>
      <label>Claims in the last 5 years <input type="number" onChange={(ev) => set("claimsLast5Years", Number(ev.target.value))} /></label>
      <label>Limit of indemnity <select onChange={(ev) => set("limitOfIndemnity", ev.target.value)}><option value="" /><option>250000</option><option>500000</option><option>1000000</option><option>5000000</option></select></label>
      <label>Postcode <input onChange={(ev) => setPostcode(ev.target.value)} /></label>
      <label>Voluntary excess <select onChange={(ev) => setVx(Number(ev.target.value))}>{VOLUNTARY_EXCESS.map((v) => <option key={v}>{v}</option>)}</select></label>
      {errors.map((m) => <p role="alert" key={m}>{m}</p>)}
      <button type="submit">Get my price</button>
    </form>
  );
}
