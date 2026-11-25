import { useState } from "react";
import { lookupPostcode } from "../../api/postcodeApi";
import type { QuoteFormProps } from "../forms";

/** Home contents (CNT) quote form. Sold in: UK. Maximum cover 250,000. */
const VOLUNTARY_EXCESS = [0, 200, 250, 1000];

export function validateCNT(a: Record<string, unknown>): string[] {
  const e: string[] = [];
  if (!(Number(a.contentsValue) >= 5000 && Number(a.contentsValue) <= 250000)) e.push("contentsValue must be between 5000 and 250000");
  if (!(Number(a.highRiskItemsValue) >= 0 && Number(a.highRiskItemsValue) <= 100000)) e.push("highRiskItemsValue must be between 0 and 100000");
  if (a.lockType === undefined || a.lockType === "") e.push("lockType is required");
  return e;
}

export function ContentsQuoteForm({ onSubmit }: QuoteFormProps) {
  const [a, setA] = useState<Record<string, unknown>>({});
  const [postcode, setPostcode] = useState("");
  const [voluntaryExcess, setVx] = useState(0);
  const [errors, setErrors] = useState<string[]>([]);
  const set = (k: string, v: unknown) => setA((s) => ({ ...s, [k]: v }));
  async function submit() {
    const e = validateCNT(a);
    if (!(await lookupPostcode(postcode)).length) e.push("We could not find that postcode");
    setErrors(e);
    if (!e.length) onSubmit({ line: "CNT", postcode, voluntaryExcess, answers: a });
  }
  return (
    <form onSubmit={(ev) => { ev.preventDefault(); submit(); }}>
      <h1>Home contents insurance quote</h1>
      <label>Total contents value <input type="number" onChange={(ev) => set("contentsValue", Number(ev.target.value))} /></label>
      <label>Jewellery, watches and art <input type="number" onChange={(ev) => set("highRiskItemsValue", Number(ev.target.value))} /></label>
      <label>Front door lock <select onChange={(ev) => set("lockType", ev.target.value)}><option value="" /><option>BS3621</option><option>OTHER</option></select></label>
      <label><input type="checkbox" onChange={(ev) => set("alarm", ev.target.checked)} /> Burglar alarm fitted?</label>
      <label>Postcode <input onChange={(ev) => setPostcode(ev.target.value)} /></label>
      <label>Voluntary excess <select onChange={(ev) => setVx(Number(ev.target.value))}>{VOLUNTARY_EXCESS.map((v) => <option key={v}>{v}</option>)}</select></label>
      {errors.map((m) => <p role="alert" key={m}>{m}</p>)}
      <button type="submit">Get my price</button>
    </form>
  );
}
