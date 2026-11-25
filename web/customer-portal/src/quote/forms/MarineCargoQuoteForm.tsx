import { useState } from "react";
import { lookupPostcode } from "../../api/postcodeApi";
import type { QuoteFormProps } from "../forms";

/** Marine cargo (MAR) quote form. Sold in: UK+US. Maximum cover 5,000,000. */
const VOLUNTARY_EXCESS = [200, 250, 400, 500];

export function validateMAR(a: Record<string, unknown>): string[] {
  const e: string[] = [];
  if (a.cargoType === undefined || a.cargoType === "") e.push("cargoType is required");
  if (!(Number(a.annualShippedValue) >= 50000 && Number(a.annualShippedValue) <= 50000000)) e.push("annualShippedValue must be between 50000 and 50000000");
  if (a.conveyance === undefined || a.conveyance === "") e.push("conveyance is required");
  if (a.incoterm === undefined || a.incoterm === "") e.push("incoterm is required");
  return e;
}

export function MarineCargoQuoteForm({ onSubmit }: QuoteFormProps) {
  const [a, setA] = useState<Record<string, unknown>>({});
  const [postcode, setPostcode] = useState("");
  const [voluntaryExcess, setVx] = useState(200);
  const [errors, setErrors] = useState<string[]>([]);
  const set = (k: string, v: unknown) => setA((s) => ({ ...s, [k]: v }));
  async function submit() {
    const e = validateMAR(a);
    if (!(await lookupPostcode(postcode)).length) e.push("We could not find that postcode");
    setErrors(e);
    if (!e.length) onSubmit({ line: "MAR", postcode, voluntaryExcess, answers: a });
  }
  return (
    <form onSubmit={(ev) => { ev.preventDefault(); submit(); }}>
      <h1>Marine cargo insurance quote</h1>
      <label>Cargo type <select onChange={(ev) => set("cargoType", ev.target.value)}><option value="" /><option>GENERAL</option><option>REFRIGERATED</option><option>HAZARDOUS</option></select></label>
      <label>Annual shipped value <input type="number" onChange={(ev) => set("annualShippedValue", Number(ev.target.value))} /></label>
      <label>Main conveyance <select onChange={(ev) => set("conveyance", ev.target.value)}><option value="" /><option>SEA</option><option>AIR</option><option>ROAD</option></select></label>
      <label>Usual Incoterm <select onChange={(ev) => set("incoterm", ev.target.value)}><option value="" /><option>FOB</option><option>CIF</option><option>DAP</option><option>DDP</option></select></label>
      <label>Postcode <input onChange={(ev) => setPostcode(ev.target.value)} /></label>
      <label>Voluntary excess <select onChange={(ev) => setVx(Number(ev.target.value))}>{VOLUNTARY_EXCESS.map((v) => <option key={v}>{v}</option>)}</select></label>
      {errors.map((m) => <p role="alert" key={m}>{m}</p>)}
      <button type="submit">Get my price</button>
    </form>
  );
}
