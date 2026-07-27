export type ApiError = { error: { code: string; message: string; details: Record<string, unknown>; request_id: string } };
export type StaffRole = "ADMIN" | "OPERATOR";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";
let accessToken: string | null = sessionStorage.getItem("access_token");
let csrfToken: string | null = sessionStorage.getItem("csrf_token");
const authChangedEvent = "staff-auth-changed";

function roleFromToken(token: string | null): StaffRole | null {
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))) as { role?: string };
    return payload.role === "ADMIN" || payload.role === "OPERATOR" ? payload.role : null;
  } catch {
    return null;
  }
}

export function setAuth(access: string | null, csrf: string | null = null) {
  accessToken = access;
  csrfToken = csrf;
  if (access) sessionStorage.setItem("access_token", access);
  else sessionStorage.removeItem("access_token");
  if (csrf) sessionStorage.setItem("csrf_token", csrf);
  else sessionStorage.removeItem("csrf_token");
  window.dispatchEvent(new Event(authChangedEvent));
}

export function isAuthenticated() { return Boolean(accessToken); }
export function getStaffRole() { return roleFromToken(accessToken); }
export function subscribeToAuth(callback: () => void) {
  window.addEventListener(authChangedEvent, callback);
  return () => window.removeEventListener(authChangedEvent, callback);
}
export function staffHome(role = getStaffRole()) {
  if (role === "ADMIN") return "/admin";
  if (role === "OPERATOR") return "/operator/scanner";
  return "/";
}

export async function logoutStaff(): Promise<void> {
  try {
    const headers = new Headers();
    if (csrfToken) headers.set("X-CSRF-Token", csrfToken);
    await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      credentials: "include",
      headers,
    });
  } finally {
    setAuth(null);
  }
}

async function refreshAuth(): Promise<boolean> {
  if (!csrfToken) return false;
  const response = await fetch(`${API_BASE}/auth/refresh`, { method: "POST", credentials: "include", headers: { "X-CSRF-Token": csrfToken } });
  if (!response.ok) { setAuth(null); return false; }
  const data = await response.json();
  setAuth(data.access_token, data.csrf_token);
  return true;
}

export async function api<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers, credentials: "include" });
  if (response.status === 401 && retry && await refreshAuth()) return api<T>(path, options, false);
  if (!response.ok) {
    const fallback: ApiError = { error: { code: "NETWORK_ERROR", message: "Не удалось выполнить запрос", details: {}, request_id: response.headers.get("X-Request-ID") ?? "unknown" } };
    throw await response.json().catch(() => fallback) as ApiError;
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function download(path: string, filename: string): Promise<void> {
  const headers = new Headers();
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  let response = await fetch(`${API_BASE}${path}`, { headers, credentials: "include" });
  if (response.status === 401 && await refreshAuth()) {
    headers.set("Authorization", `Bearer ${accessToken}`);
    response = await fetch(`${API_BASE}${path}`, { headers, credentials: "include" });
  }
  if (!response.ok) throw await response.json() as ApiError;
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function errorMessage(error: unknown): string {
  return (error as ApiError)?.error?.message ?? "Произошла непредвиденная ошибка";
}

export const EVENT_SLUG = import.meta.env.VITE_EVENT_SLUG ?? "freshman-day-2026";
