import type { components } from "./schema";
import { ApiError, toApiError } from "./errors";

type TokenOut = components["schemas"]["TokenOut"];
type UserOut = components["schemas"]["UserOut"];
type AuthSnapshot = { accessToken: string | null; user: UserOut | null };

const apiBase = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
if (!apiBase) {
  throw new Error("NEXT_PUBLIC_API_URL is required at build time");
}

let accessToken: string | null = null;
let refreshPromise: Promise<TokenOut | null> | null = null;
const listeners = new Set<(snapshot: AuthSnapshot) => void>();

function publish(user: UserOut | null = null) {
  const snapshot = { accessToken, user };
  listeners.forEach((listener) => listener(snapshot));
}

export function subscribeAuth(listener: (snapshot: AuthSnapshot) => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function clearAuth() {
  accessToken = null;
  publish(null);
}

function setAuth(token: TokenOut) {
  accessToken = token.access_token;
  publish(token.user);
}

function isAuthEndpoint(path: string) {
  return /^\/v1\/auth\/(login|register|refresh|telegram\/)/.test(path);
}

export function refreshAccessToken(): Promise<TokenOut | null> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const response = await fetch(`${apiBase}/v1/auth/refresh`, {
          method: "POST",
          credentials: "include",
          headers: { Accept: "application/json" },
        });
        if (!response.ok) {
          clearAuth();
          return null;
        }
        const token = (await response.json()) as TokenOut;
        setAuth(token);
        return token;
      } catch {
        clearAuth();
        return null;
      } finally {
        refreshPromise = null;
      }
    })();
  }
  return refreshPromise;
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  if (!path.startsWith("/v1/")) {
    throw new Error("API path must start with /v1/");
  }

  const makeRequest = () => {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");
    if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
    else headers.delete("Authorization");
    return fetch(`${apiBase}${path}`, { ...init, headers, credentials: "include" });
  };

  let response = await makeRequest();
  if (response.status === 401 && !isAuthEndpoint(path)) {
    const originalError = await toApiError(response);
    if (originalError.code === "token_reused") {
      clearAuth();
      throw originalError;
    }
    const refreshed = await refreshAccessToken();
    if (!refreshed) throw originalError;
    response = await makeRequest();
  }

  if (!response.ok) throw await toApiError(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function signOut() {
  try {
    await apiRequest<void>("/v1/auth/logout", { method: "POST" });
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 401) throw error;
  } finally {
    clearAuth();
  }
}
