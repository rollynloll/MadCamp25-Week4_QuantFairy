const RAW_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
export const API_BASE_URL = RAW_BASE ? RAW_BASE.replace(/\/$/, "") : "";

const normalizePath = (path: string) => {
  if (path.startsWith("/api/v1")) return path;
  if (path.startsWith("/")) return `/api/v1${path}`;
  return `/api/v1/${path}`;
};

export const buildApiUrl = (path: string, params?: Record<string, unknown>) => {
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
