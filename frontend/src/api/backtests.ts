import { API_BASE_URL } from "@/api/base";
import type { BacktestJob, BacktestResultsResponse } from "@/types/backtest";

const JSON_HEADERS = { "Content-Type": "application/json; charset=utf-8" };

const TOKEN_KEYS = ["token", "accessToken", "access_token", "authToken", "jwt"] as const;

function readToken(): string | null {
  const envToken = import.meta.env.VITE_API_TOKEN;
  if (envToken) return envToken;

  for (const key of TOKEN_KEYS) {
    const fromLocal = localStorage.getItem(key);
    if (fromLocal) return fromLocal;
    const fromSession = sessionStorage.getItem(key);
    if (fromSession) return fromSession;
  }
  return null;
}

function buildHeaders(): HeadersInit {
  const headers: Record<string, string> = { ...JSON_HEADERS };
  const token = readToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

export function hasAuthToken() {
  return Boolean(readToken());
}

async function handleJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.error?.message ?? `Request failed (${res.status})`;
    throw new Error(message);
  }
  return res.json();
}

export async function getBacktestJob(backtestId: string) {
  const res = await fetch(`${API_BASE_URL}/backtests/${backtestId}`, {
    headers: buildHeaders(),
  });
  return handleJson<{ job: BacktestJob }>(res);
}

export async function getBacktestResults(backtestId: string) {
  const res = await fetch(`${API_BASE_URL}/backtests/${backtestId}/results`, {
    headers: buildHeaders(),
  });
  return handleJson<BacktestResultsResponse>(res);
}

export interface BacktestListQuery {
  limit?: number;
  cursor?: string;
  status?: "queued" | "running" | "done" | "failed" | "canceled";
  mode?: "single" | "batch" | "ensemble";
  sort?: "created_at" | "updated_at";
  order?: "asc" | "desc";
}

export interface BacktestListItem {
  backtest_id: string;
  mode: "single" | "batch" | "ensemble";
  status: "queued" | "running" | "done" | "failed" | "canceled";
  created_at?: string;
  updated_at?: string;
}

export interface BacktestListResponse {
  items: BacktestListItem[];
  next_cursor?: string | null;
}

function buildQuery(params: BacktestListQuery) {
  const search = new URLSearchParams();
  if (params.limit !== undefined) search.set("limit", String(params.limit));
  if (params.cursor) search.set("cursor", params.cursor);
  if (params.status) search.set("status", params.status);
  if (params.mode) search.set("mode", params.mode);
  if (params.sort) search.set("sort", params.sort);
  if (params.order) search.set("order", params.order);
  return search.toString();
}

export async function getBacktests(
  params: BacktestListQuery = {}
): Promise<BacktestListResponse> {
  const query = buildQuery(params);
  const url = query
    ? `${API_BASE_URL}/backtests?${query}`
    : `${API_BASE_URL}/backtests`;

  const res = await fetch(url, {
    headers: buildHeaders(),
  });
  return handleJson<BacktestListResponse>(res);
}
