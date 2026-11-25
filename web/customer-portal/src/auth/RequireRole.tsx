import type { ReactNode } from "react";
import { useSession } from "./AuthProvider";

export function RequireRole({ role, children }: { role: "CUSTOMER" | "BROKER"; children: ReactNode }) {
  const s = useSession();
  if (!s) return <p>Signing you in…</p>;
  if (!s.roles.includes(role)) return <p role="alert">You do not have access to this page.</p>;
  return <>{children}</>;
}
