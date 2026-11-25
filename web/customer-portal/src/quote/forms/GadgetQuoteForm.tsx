import { useState } from "react";
import { lookupPostcode } from "../../api/postcodeApi";
import type { QuoteFormProps } from "../forms";

/** Gadget (GDG) quote form. Sold in: UK. Maximum cover 4,000. */
const VOLUNTARY_EXCESS = [0, 100, 400, 500];

export function validateGDG(a: Record<string, unknown>): string[] {
  const e: string[] = [];
  if (a.deviceType === undefined || a.deviceType === "") e.push("deviceType is required");
  if (!(Number(a.purchasePrice) >= 50 && Number(a.purchasePrice) <= 4000)) e.push("purchasePrice must be between 50 and 4000");
  if ((Date.now() - new Date(String(a.purchaseDate)).getTime()) / 86400000 > 540) e.push("purchaseDate: devices must be under 540 days old");
  return e;
}

export function GadgetQuoteForm({ onSubmit }: QuoteFormProps) {
  const [a, setA] = useState<Record<string, unknown>>({});
  const [postcode, setPostcode] = useState("");
  const [voluntaryExcess, setVx] = useState(0);
  const [errors, setErrors] = useState<string[]>([]);
  const set = (k: string, v: unknown) => setA((s) => ({ ...s, [k]: v }));
  async function submit() {
    const e = validateGDG(a);
    if (!(await lookupPostcode(postcode)).length) e.push("We could not find that postcode");
    setErrors(e);
    if (!e.length) onSubmit({ line: "GDG", postcode, voluntaryExcess, answers: a });
  }
  return (
    <form onSubmit={(ev) => { ev.preventDefault(); submit(); }}>
      <h1>Gadget insurance quote</h1>
      <label>Device type <select onChange={(ev) => set("deviceType", ev.target.value)}><option value="" /><option>PHONE</option><option>TABLET</option><option>LAPTOP</option><option>WATCH</option><option>HEADPHONES</option></select></label>
      <label>Purchase price <input type="number" onChange={(ev) => set("purchasePrice", Number(ev.target.value))} /></label>
      <label>Purchase date <input type="date" onChange={(ev) => set("purchaseDate", ev.target.value)} /></label>
      <label>Postcode <input onChange={(ev) => setPostcode(ev.target.value)} /></label>
      <label>Voluntary excess <select onChange={(ev) => setVx(Number(ev.target.value))}>{VOLUNTARY_EXCESS.map((v) => <option key={v}>{v}</option>)}</select></label>
      {errors.map((m) => <p role="alert" key={m}>{m}</p>)}
      <button type="submit">Get my price</button>
    </form>
  );
}
