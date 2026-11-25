import { useState } from "react";
import { lookupPostcode } from "../../api/postcodeApi";
import type { QuoteFormProps } from "../forms";

/** Pet (PET) quote form. Sold in: UK. Maximum cover 15,000. */
const VOLUNTARY_EXCESS = [200, 400, 750, 1000];

export function validatePET(a: Record<string, unknown>): string[] {
  const e: string[] = [];
  if (a.species === undefined || a.species === "") e.push("species is required");
  if (a.breed === undefined || a.breed === "") e.push("breed is required");
  if (!(Number(a.ageYears) >= 0 && Number(a.ageYears) <= 14)) e.push("ageYears must be between 0 and 14");
  return e;
}

export function PetQuoteForm({ onSubmit }: QuoteFormProps) {
  const [a, setA] = useState<Record<string, unknown>>({});
  const [postcode, setPostcode] = useState("");
  const [voluntaryExcess, setVx] = useState(200);
  const [errors, setErrors] = useState<string[]>([]);
  const set = (k: string, v: unknown) => setA((s) => ({ ...s, [k]: v }));
  async function submit() {
    const e = validatePET(a);
    if (!(await lookupPostcode(postcode)).length) e.push("We could not find that postcode");
    setErrors(e);
    if (!e.length) onSubmit({ line: "PET", postcode, voluntaryExcess, answers: a });
  }
  return (
    <form onSubmit={(ev) => { ev.preventDefault(); submit(); }}>
      <h1>Pet insurance quote</h1>
      <label>Species <select onChange={(ev) => set("species", ev.target.value)}><option value="" /><option>DOG</option><option>CAT</option><option>RABBIT</option></select></label>
      <label>Breed <input type="text" onChange={(ev) => set("breed", ev.target.value)} /></label>
      <label>Age in years <input type="number" onChange={(ev) => set("ageYears", Number(ev.target.value))} /></label>
      <label><input type="checkbox" onChange={(ev) => set("microchipped", ev.target.checked)} /> Microchipped?</label>
      <label>Postcode <input onChange={(ev) => setPostcode(ev.target.value)} /></label>
      <label>Voluntary excess <select onChange={(ev) => setVx(Number(ev.target.value))}>{VOLUNTARY_EXCESS.map((v) => <option key={v}>{v}</option>)}</select></label>
      {errors.map((m) => <p role="alert" key={m}>{m}</p>)}
      <button type="submit">Get my price</button>
    </form>
  );
}
