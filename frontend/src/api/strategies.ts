import { API_BASE_URL } from "@/api/base";
import type {
  PublicStrategyDetail,
  PublicStrategyListResponse,
  PublicStrategyValidationResponse,
  RiskLevel
} from "@/types/strategy";

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

function buildQuery(params: PublicStrategiesQuery) {
  const search = new URLSearchParams();
  if (params.limit !== undefined) search.set("limit", String(params.limit));
  if (params.cursor) search.set("cursor", params.cursor);
  if (params.q) search.set("q", params.q);
  if (params.tag) search.set("tag", params.tag);
  if (params.category) search.set("category", params.category);
  if (params.risk_level) search.set("risk_level", params.risk_level);
  if (params.sort) search.set("sort", params.sort);
  if (params.order) search.set("order", params.order);
  return search.toString();
}

export async function getPublicStrategies(
  params: PublicStrategiesQuery = {}
): Promise<PublicStrategyListResponse> {
  const query = buildQuery(params);
  const url = query
    ? `${API_BASE_URL}/public-strategies?${query}`
    : `${API_BASE_URL}/public-strategies`;

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

export async function getPublicStrategy(
  publicStrategyId: string
): Promise<PublicStrategyDetail> {
  const res = await fetch(
    `${API_BASE_URL}/public-strategies/${publicStrategyId}`,
    {
      headers: { "Content-Type": "application/json" }
    }
  );

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
  const res = await fetch(
    `${API_BASE_URL}/public-strategies/${publicStrategyId}/validate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ params })
    }
  );

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message =
      body?.error?.message ?? `Failed to validate params (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}
