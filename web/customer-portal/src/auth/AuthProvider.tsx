import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export interface Session { token: string; roles: string[]; customerId: string }
const Ctx = createContext<Session | null>(null);

/** OIDC login against the Corvane identity provider. The access token lives in memory only, never in localStorage. */
export function AuthProvider({ issuer, clientId, children }: { issuer: string; clientId: string; children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  useEffect(() => {
    fetch(`${issuer}/session?client_id=${clientId}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((s) => s && setSession({ token: s.access_token, roles: s.roles ?? [], customerId: s.sub }));
  }, [issuer, clientId]);
  return <Ctx.Provider value={session}>{children}</Ctx.Provider>;
}

export const useSession = () => useContext(Ctx);
