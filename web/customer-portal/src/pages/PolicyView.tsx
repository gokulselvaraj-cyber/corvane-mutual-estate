import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getPolicy } from "../api/policyApi";
import { useToken } from "../api/http";
import { fullName } from "../model/Customer";
import type { PolicySummary } from "../model/Policy";

export function PolicyView() {
  const { policyNumber } = useParams();
  const token = useToken();
  const [p, setP] = useState<PolicySummary>();
  useEffect(() => { getPolicy(token, policyNumber!).then(setP); }, [token, policyNumber]);
  if (!p) return <p>Loading…</p>;
  return (
    <main>
      <h1>{p.policyNumber}</h1>
      <p>Policyholder: {fullName(p.holder)}</p>
      <p>Cover from {p.inceptionDate} to {p.expiryDate}</p>
      <p>Excess: compulsory {p.compulsoryExcess} + voluntary {p.voluntaryExcess}</p>
      <p>Status: {p.status}</p>
    </main>
  );
}
