import type { FnolState } from "../FnolWizard";

export function Review({ state, next, back }: { state: FnolState; next: () => void; back: () => void }) {
  const i = state.incident!;
  return (
    <section>
      <h2>Check your claim</h2>
      <dl>
        <dt>Policy</dt><dd>{state.policyNumber}</dd>
        <dt>Loss date</dt><dd>{i.lossDate}</dd>
        <dt>Estimated amount</dt><dd>{i.estimatedAmount}</dd>
        <dt>Photos</dt><dd>{state.photos.length}</dd>
      </dl>
      <p>Claims under our auto-approval limit may be settled without an adjuster.</p>
      <button onClick={back}>Back</button><button onClick={next}>Submit claim</button>
    </section>
  );
}
