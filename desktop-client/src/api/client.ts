export const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export type ApiOptions = {
  token?: string | null;
  method?: string;
  body?: object | FormData;
};

export async function request<T>(path: string, options: ApiOptions = {}): Promise<T> {
  let body: BodyInit | undefined;
  if (options.body instanceof FormData) {
    body = options.body;
  } else if (options.body !== undefined) {
    body = JSON.stringify(options.body);
  }
  const isFormData = body instanceof FormData;
  const headers: Record<string, string> = {};
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }
  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }
  const response = await fetch(`${API_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof detail.detail === "string" ? detail.detail : "Request failed");
  }
  return response.json() as Promise<T>;
}

export function fileUrl(path: string, download = false) {
  const url = new URL(path.startsWith("http") ? path : `${API_URL}${path}`);
  if (download) {
    url.searchParams.set("download", "1");
  }
  return url.toString();
}

export function wsUrl(token: string) {
  const url = new URL(API_URL);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = "/ws";
  url.search = `token=${encodeURIComponent(token)}`;
  return url.toString();
}
