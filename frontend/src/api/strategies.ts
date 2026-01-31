import { buildApiUrl } from "@/api/base";
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
