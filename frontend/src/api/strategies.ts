import { buildApiUrl } from "@/api/base";
import type {
  PublicStrategyDetail,
  PublicStrategyListResponse,
  PublicStrategyValidationResponse,
  RiskLevel,
  MyStrategyListResponse
} from "@/types/strategy";

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

function buildAuthHeaders(): HeadersInit {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = readToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

export interface PublicStrategiesQuery {
  limit?: number;
  cursor?: string;
  q?: string;
  tag?: string;
  category?: string;
  risk_level?: RiskLevel;
  sort?: "updated_at" | "adds_count" | "name";
  order?: "asc" | "desc";
}

export async function getPublicStrategies(
  params: PublicStrategiesQuery = {}
): Promise<PublicStrategyListResponse> {
  const url = buildApiUrl("/public-strategies", params);

  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message =
      body?.error?.message ?? `Failed to load strategies (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}

export async function getMyStrategies(): Promise<MyStrategyListResponse> {
  const res = await fetch(buildApiUrl("/my-strategies"), {
    headers: buildAuthHeaders(),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message =
      body?.error?.message ?? `Failed to load my strategies (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}

export async function getPublicStrategy(
  publicStrategyId: string
): Promise<PublicStrategyDetail> {
  const res = await fetch(buildApiUrl(`/public-strategies/${publicStrategyId}`), {
    headers: { "Content-Type": "application/json" }
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message =
      body?.error?.message ?? `Failed to load strategy (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}

export async function validatePublicStrategyParams(
  publicStrategyId: string,
  params: Record<string, unknown>
): Promise<PublicStrategyValidationResponse> {
  const res = await fetch(buildApiUrl(`/public-strategies/${publicStrategyId}/validate`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ params })
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message =
      body?.error?.message ?? `Failed to validate params (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}
