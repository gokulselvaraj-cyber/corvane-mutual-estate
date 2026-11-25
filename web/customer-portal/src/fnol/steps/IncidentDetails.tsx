import { useState } from "react";
import type { IncidentDetails } from "../../api/claimsApi";
import type { FnolState } from "../FnolWizard";

/** Loss date may not be in the future or more than 180 days ago (claims-service enforces per-line windows too). */
export function validateIncident(i: IncidentDetails, today = new Date()): string[] {
  const errors: string[] = [];
  const loss = new Date(i.lossDate);
  if (loss > today) errors.push("The loss date cannot be in the future.");
  if ((today.getTime() - loss.getTime()) / 86400000 > 180) errors.push("Losses older than 180 days must be reported by phone.");
  if (i.description.trim().length < 20) errors.push("Please describe what happened in at least 20 characters.");
  if (i.injuryInvolved && !i.injuryNotes) errors.push("Please tell us about the injury.");
  if (i.estimatedAmount <= 0) errors.push("Enter an estimated amount.");
  return errors;
}

export function IncidentDetailsStep({ update, next, back }: { state: FnolState; update: (p: Partial<FnolState>) => void; next: () => void; back: () => void }) {
  const [i, setI] = useState<IncidentDetails>({ lossDate: "", lossCause: "", description: "", injuryInvolved: false, estimatedAmount: 0, thirdPartyInvolved: false });
  const [errors, setErrors] = useState<string[]>([]);
  const go = () => { const e = validateIncident(i); setErrors(e); if (!e.length) { update({ incident: i }); next(); } };
  return (
    <section>
      <input type="date" aria-label="Loss date" onChange={(e) => setI({ ...i, lossDate: e.target.value })} />
      <textarea aria-label="What happened" onChange={(e) => setI({ ...i, description: e.target.value })} />
      <label><input type="checkbox" onChange={(e) => setI({ ...i, injuryInvolved: e.target.checked })} /> Someone was injured</label>
      {i.injuryInvolved && <textarea aria-label="Injury details" onChange={(e) => setI({ ...i, injuryNotes: e.target.value })} />}
      <input type="number" aria-label="Estimated amount" onChange={(e) => setI({ ...i, estimatedAmount: Number(e.target.value) })} />
      {errors.map((e) => <p role="alert" key={e}>{e}</p>)}
      <button onClick={back}>Back</button><button onClick={go}>Continue</button>
    </section>
  );
}
