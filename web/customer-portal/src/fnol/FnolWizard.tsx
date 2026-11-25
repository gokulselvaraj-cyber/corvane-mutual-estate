import { useState } from "react";
import { PolicyLookup } from "./steps/PolicyLookup";
import { IncidentDetailsStep } from "./steps/IncidentDetails";
import { DamageAndPhotos } from "./steps/DamageAndPhotos";
import { Review } from "./steps/Review";
import { Submit } from "./steps/Submit";
import type { IncidentDetails } from "../api/claimsApi";

/** First notice of loss: the five steps, in order. Journey J1 starts here. */
export const STEPS = ["PolicyLookup", "IncidentDetails", "DamageAndPhotos", "Review", "Submit"] as const;
export type Step = (typeof STEPS)[number];

export interface FnolState {
  policyNumber?: string;
  draftId?: string;
  incident?: IncidentDetails;
  photos: File[];
}

export function FnolWizard() {
  const [step, setStep] = useState<Step>("PolicyLookup");
  const [state, setState] = useState<FnolState>({ photos: [] });
  const next = () => setStep(STEPS[Math.min(STEPS.indexOf(step) + 1, STEPS.length - 1)]);
  const back = () => setStep(STEPS[Math.max(STEPS.indexOf(step) - 1, 0)]);
  const update = (p: Partial<FnolState>) => setState((s) => ({ ...s, ...p }));

  return (
    <main aria-label="Report a claim">
      <ol className="steps">{STEPS.map((s) => <li key={s} aria-current={s === step}>{s}</li>)}</ol>
      {step === "PolicyLookup" && <PolicyLookup state={state} update={update} next={next} />}
      {step === "IncidentDetails" && <IncidentDetailsStep state={state} update={update} next={next} back={back} />}
      {step === "DamageAndPhotos" && <DamageAndPhotos state={state} update={update} next={next} back={back} />}
      {step === "Review" && <Review state={state} next={next} back={back} />}
      {step === "Submit" && <Submit state={state} />}
    </main>
  );
}
