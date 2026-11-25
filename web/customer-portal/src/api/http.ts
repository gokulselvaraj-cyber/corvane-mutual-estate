import { useSession } from "../auth/AuthProvider";

export class ApiError extends Error {
  constructor(public status: number, public body: string) { super(`API ${status}`); }
}

const TIMEOUT_MS = 15000;

/** All calls go through the edge path /api/...; nginx forwards to the services. */
export async function call<T>(token: string | undefined, path: string, init: RequestInit = {}): Promise<T> {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(path, {
      ...init,
      signal: ctl.signal,
      headers: { ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
                 ...(token ? { Authorization: `Bearer ${token}` } : {}), ...init.headers },
    });
    if (!res.ok) throw new ApiError(res.status, await res.text());
    return (await res.json()) as T;
  } finally {
    clearTimeout(t);
  }
}

export const useToken = () => useSession()?.token;
