import { useState } from "react";
import { lookupPostcode } from "../../api/postcodeApi";
import type { QuoteFormProps } from "../forms";

/** Motor (MTR) quote form. Sold in: UK+US. Maximum cover 150,000. */
const VOLUNTARY_EXCESS = [200, 400, 500, 1000];

export function validateMTR(a: Record<string, unknown>): string[] {
  const e: string[] = [];
  if (!/^[A-Z0-9 ]{2,8}$/.test(String(a.vehicleRegistration ?? ""))) e.push("vehicleRegistration is not valid");
  if (!(Number(a.vehicleValue) >= 500 && Number(a.vehicleValue) <= 150000)) e.push("vehicleValue must be between 500 and 150000");
  if (!(Number(a.annualMileage) >= 1000 && Number(a.annualMileage) <= 50000)) e.push("annualMileage must be between 1000 and 50000");
  if (!(Number(a.mainDriverAge) >= 17 && Number(a.mainDriverAge) <= 99)) e.push("mainDriverAge must be between 17 and 99");
  if (a.overnightParking === undefined || a.overnightParking === "") e.push("overnightParking is required");
  return e;
}

export function MotorQuoteForm({ onSubmit }: QuoteFormProps) {
  const [a, setA] = useState<Record<string, unknown>>({});
  const [postcode, setPostcode] = useState("");
  const [voluntaryExcess, setVx] = useState(200);
  const [errors, setErrors] = useState<string[]>([]);
  const set = (k: string, v: unknown) => setA((s) => ({ ...s, [k]: v }));
  async function submit() {
    const e = validateMTR(a);
    if (!(await lookupPostcode(postcode)).length) e.push("We could not find that postcode");
    setErrors(e);
    if (!e.length) onSubmit({ line: "MTR", postcode, voluntaryExcess, answers: a });
  }
  return (
    <form onSubmit={(ev) => { ev.preventDefault(); submit(); }}>
      <h1>Motor insurance quote</h1>
      <label>Vehicle registration <input type="text" onChange={(ev) => set("vehicleRegistration", ev.target.value)} /></label>
      <label>Vehicle value <input type="number" onChange={(ev) => set("vehicleValue", Number(ev.target.value))} /></label>
      <label>Annual mileage <input type="number" onChange={(ev) => set("annualMileage", Number(ev.target.value))} /></label>
      <label>Main driver age <input type="number" onChange={(ev) => set("mainDriverAge", Number(ev.target.value))} /></label>
      <label>Where is it kept overnight? <select onChange={(ev) => set("overnightParking", ev.target.value)}><option value="" /><option>DRIVEWAY</option><option>GARAGE</option><option>STREET</option></select></label>
      <label>Postcode <input onChange={(ev) => setPostcode(ev.target.value)} /></label>
      <label>Voluntary excess <select onChange={(ev) => setVx(Number(ev.target.value))}>{VOLUNTARY_EXCESS.map((v) => <option key={v}>{v}</option>)}</select></label>
      {errors.map((m) => <p role="alert" key={m}>{m}</p>)}
      <button type="submit">Get my price</button>
    </form>
  );
}
