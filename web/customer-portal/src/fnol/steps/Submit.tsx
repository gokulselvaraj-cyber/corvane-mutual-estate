import { useEffect, useState } from "react";
import { registerClaim, type RegisteredClaim } from "../../api/claimsApi";
import { useToken } from "../../api/http";
import type { FnolState } from "../FnolWizard";

export function Submit({ state }: { state: FnolState }) {
  const token = useToken();
  const [result, setResult] = useState<RegisteredClaim>();
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    registerClaim(token, state.draftId!, state.incident!).then(setResult, () => setFailed(true));
  }, [token, state]);
  if (failed) return <p role="alert">We could not submit your claim. Please call 0800 000 0000.</p>;
  if (!result) return <p>Submitting…</p>;
  return (
    <section>
      <h2>Claim {result.reference} received</h2>
      {result.status === "AUTO_APPROVED" && <p>Good news: your claim has been approved. Payment usually arrives within 3 working days.</p>}
      {result.status === "REFERRED" && <p>An adjuster will contact you within 2 working days.</p>}
      {result.status === "REGISTERED" && <p>We are reviewing your claim.</p>}
    </section>
  );
}
