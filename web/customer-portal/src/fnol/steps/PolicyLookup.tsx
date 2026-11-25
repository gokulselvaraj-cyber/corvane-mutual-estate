import { useState } from "react";
import { getPolicy } from "../../api/policyApi";
import { createDraft } from "../../api/claimsApi";
import { useToken } from "../../api/http";
import type { FnolState } from "../FnolWizard";

const POLICY_NUMBER = /^CVM-(MTR|HOM|CNT|TRV|PET|LLD|MAR|CPR|PLB|PIN|CYB|GDG)-\d{7}$/;

export function PolicyLookup({ update, next }: { state: FnolState; update: (p: Partial<FnolState>) => void; next: () => void }) {
  const token = useToken();
  const [value, setValue] = useState("");
  const [error, setError] = useState<string>();
  async function find() {
    if (!POLICY_NUMBER.test(value)) return setError("Policy numbers look like CVM-MTR-0012345.");
    const policy = await getPolicy(token, value);
    if (policy.status !== "BOUND") return setError("This policy is not active, so a claim cannot be reported online.");
    const draft = await createDraft(token, value);
    update({ policyNumber: value, draftId: draft.draftId });
    next();
  }
  return (
    <section>
      <label>Policy number <input value={value} onChange={(e) => setValue(e.target.value.toUpperCase())} /></label>
      {error && <p role="alert">{error}</p>}
      <button onClick={find}>Find my policy</button>
    </section>
  );
}
