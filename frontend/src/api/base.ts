const RAW_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();

const resolveBaseUrl = () => {
  if (RAW_BASE) return RAW_BASE.replace(/\/$/, "");
  if (typeof window !== "undefined") {
    const { hostname, port } = window.location;
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      if (port === "5173" || port === "3000" || port === "4173") {
        return "http://localhost:8000";
      }
    }
  }
  return "";
};

export const API_BASE_URL = resolveBaseUrl();

const normalizePath = (path: string) => {
  if (path.startsWith("/api/v1")) return path;
  if (path.startsWith("/")) return `/api/v1${path}`;
  return `/api/v1/${path}`;
};


export const buildApiUrl = (
  path: string,
  params?: Record<string, any>
) => {
  const normalized = normalizePath(path);
  if (!API_BASE_URL) {
    if (!params) return normalized;
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value === undefined || value === null) return;
      qs.set(key, String(value));
    });
    const query = qs.toString();
    return query ? `${normalized}?${query}` : normalized;
  }

  const url = new URL(normalized, API_BASE_URL);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value === undefined || value === null) return;
      url.searchParams.set(key, String(value));
    });
  }
  return url.toString();
};
