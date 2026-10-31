import type { ApiErrorBody } from "@/types/api";

const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "/api";
const IDENTITY_KEY = "dealbridge.demoUserId";

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details: Record<string, unknown>;
  readonly requestId: string | null;

  constructor(status: number, code: string, message: string, details: Record<string, unknown>, requestId: string | null) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
    this.requestId = requestId;
  }
}

export function getStoredUserId(): string | null {
  try {
    return localStorage.getItem(IDENTITY_KEY);
  } catch {
    return null;
  }
}

export function storeUserId(id: string | null) {
  try {
    if (id) localStorage.setItem(IDENTITY_KEY, id);
    else localStorage.removeItem(IDENTITY_KEY);
  } catch {
    /* storage unavailable: identity lasts for this tab only */
  }
}

type Body = Record<string, unknown> | unknown[] | FormData | undefined;

async function parseError(res: Response): Promise<ApiError> {
  const rid = res.headers.get("X-Request-Id");
  try {
    const body = (await res.json()) as ApiErrorBody;
    if (body?.error?.code) return new ApiError(res.status, body.error.code, body.error.message, body.error.details ?? {}, rid);
  } catch {
    /* non-JSON error */
  }
  return new ApiError(res.status, "HTTP_ERROR", `Request failed with status ${res.status}.`, {}, rid);
}

export async function request<T>(method: string, path: string, body?: Body, signal?: AbortSignal): Promise<T> {
  const headers: Record<string, string> = {};
  const uid = getStoredUserId();
  if (uid) headers["X-Demo-User-Id"] = uid;
  let payload: BodyInit | undefined;
  if (body instanceof FormData) payload = body;
  else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, { method, headers, body: payload, signal });
  } catch {
    throw new ApiError(0, "NETWORK_ERROR", "The DealBridge API could not be reached. Is the backend running?", {}, null);
  }
  if (!res.ok) throw await parseError(res);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export async function downloadFile(path: string, fallbackName: string): Promise<void> {
  const headers: Record<string, string> = {};
  const uid = getStoredUserId();
  if (uid) headers["X-Demo-User-Id"] = uid;
  const res = await fetch(`${BASE}${path}`, { headers });
  if (!res.ok) throw await parseError(res);
  const blob = await res.blob();
  const cd = res.headers.get("Content-Disposition") ?? "";
  const match = /filename="?([^";]+)"?/.exec(cd);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = match?.[1] ?? fallbackName;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export const api = {
  get: <T,>(path: string, signal?: AbortSignal) => request<T>("GET", path, undefined, signal),
  post: <T,>(path: string, body?: Body) => request<T>("POST", path, body ?? {}),
  patch: <T,>(path: string, body?: Body) => request<T>("PATCH", path, body ?? {}),
  del: <T,>(path: string) => request<T>("DELETE", path),
};
