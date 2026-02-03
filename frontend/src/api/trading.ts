import { buildApiUrl } from "@/api/base";
import type { TradingOrdersResponse, TradingOrderDetail, TradingPositionsResponse } from "@/types/trading";

export type OrderScope = "open" | "filled" | "all";

export async function getTradingOrders(params: {
  scope: OrderScope;
  limit?: number;
  cursor?: string | null;
}): Promise<TradingOrdersResponse> {
  const { scope, limit = 50, cursor } = params;

  const res = await fetch(buildApiUrl("/trading/orders", {
    scope,
    limit,
    cursor: cursor ?? undefined
  }), {
    headers: { "Content-Type": "application/json" }
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message =
      body?.error?.message ?? `Failed to load orders (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}

export async function getTradingOrder(orderId: string): Promise<TradingOrderDetail> {
  const res = await fetch(buildApiUrl(`/trading/orders/${orderId}`), {
    headers: { "Content-Type": "application/json" }
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message =
      body?.error?.message ?? `Failed to load order (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}

export async function getTradingPositions(): Promise<TradingPositionsResponse> {
  const res = await fetch(buildApiUrl("/trading/positions"), {
    headers: { "Content-Type": "application/json" }
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message =
      body?.error?.message ?? `Failed to load positions (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}