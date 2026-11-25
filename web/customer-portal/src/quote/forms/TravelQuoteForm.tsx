import { useState } from "react";
import { lookupPostcode } from "../../api/postcodeApi";
import type { QuoteFormProps } from "../forms";

/** Travel (TRV) quote form. Sold in: UK+US. Maximum cover 10,000,000. */
const VOLUNTARY_EXCESS = [0, 150, 200, 500];

export function validateTRV(a: Record<string, unknown>): string[] {
  const e: string[] = [];
  if (a.tripType === undefined || a.tripType === "") e.push("tripType is required");
  if (a.destination === undefined || a.destination === "") e.push("destination is required");
  if (!(Number(a.travellers) >= 1 && Number(a.travellers) <= 10)) e.push("travellers must be between 1 and 10");
  if (!(Number(a.oldestTravellerAge) >= 0 && Number(a.oldestTravellerAge) <= 85)) e.push("oldestTravellerAge must be between 0 and 85");
  return e;
}

export function TravelQuoteForm({ onSubmit }: QuoteFormProps) {
  const [a, setA] = useState<Record<string, unknown>>({});
  const [postcode, setPostcode] = useState("");
  const [voluntaryExcess, setVx] = useState(0);
  const [errors, setErrors] = useState<string[]>([]);
  const set = (k: string, v: unknown) => setA((s) => ({ ...s, [k]: v }));
  async function submit() {
    const e = validateTRV(a);
    if (!(await lookupPostcode(postcode)).length) e.push("We could not find that postcode");
    setErrors(e);
    if (!e.length) onSubmit({ line: "TRV", postcode, voluntaryExcess, answers: a });
  }
  return (
    <form onSubmit={(ev) => { ev.preventDefault(); submit(); }}>
      <h1>Travel insurance quote</h1>
      <label>Single trip or annual <select onChange={(ev) => set("tripType", ev.target.value)}><option value="" /><option>SINGLE</option><option>ANNUAL</option></select></label>
      <label>Destination <select onChange={(ev) => set("destination", ev.target.value)}><option value="" /><option>EUROPE</option><option>WORLDWIDE_EX_US</option><option>WORLDWIDE</option></select></label>
      <label>Number of travellers <input type="number" onChange={(ev) => set("travellers", Number(ev.target.value))} /></label>
      <label>Age of the oldest traveller <input type="number" onChange={(ev) => set("oldestTravellerAge", Number(ev.target.value))} /></label>
      <label><input type="checkbox" onChange={(ev) => set("preExistingConditions", ev.target.checked)} /> Any pre-existing medical conditions?</label>
      <label>Postcode <input onChange={(ev) => setPostcode(ev.target.value)} /></label>
      <label>Voluntary excess <select onChange={(ev) => setVx(Number(ev.target.value))}>{VOLUNTARY_EXCESS.map((v) => <option key={v}>{v}</option>)}</select></label>
      {errors.map((m) => <p role="alert" key={m}>{m}</p>)}
      <button type="submit">Get my price</button>
    </form>
  );
}
