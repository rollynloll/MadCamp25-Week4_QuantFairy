// src/api/userStrategies.ts
import { buildApiUrl } from "@/api/base";
import type { Env, UserStrategiesResponse, UserStrategyDetailResponse } from "@/types/portfolio";

async function parseErrorMessage(res: Response, fallback: string) {
  const body = await res.json().catch(() => null);
  return body?.error?.message ?? fallback;
}

export async function getUserStrategies(env: Env): Promise<UserStrategiesResponse> {
  const res = await fetch(buildApiUrl("/user-strategies", { env }), {
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(await parseErrorMessage(res, `Failed to load strategies (${res.status})`));
  return res.json();
}

export async function getUserStrategyDetail(env: Env, userStrategyId: string): Promise<UserStrategyDetailResponse> {
  const res = await fetch(buildApiUrl(`/user-strategies/${userStrategyId}`, { env }), {
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(await parseErrorMessage(res, `Failed to load strategy detail (${res.status})`));
  return res.json();
}

export async function patchUserStrategy(
  env: Env,
  userStrategyId: string,
  body: { name?: string; params?: Record<string, any>; risk_limits?: Record<string, any> }
): Promise<{ ok: true; user_strategy_id: string; updated_at: string }> {
  const res = await fetch(buildApiUrl(`/user-strategies/${userStrategyId}`, { env }), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await parseErrorMessage(res, `Failed to save strategy (${res.status})`));
  return res.json();
}

export async function setUserStrategyState(
  env: Env,
  userStrategyId: string,
  action: "start" | "pause" | "stop"
): Promise<{ ok: true; user_strategy_id: string; state: "running" | "paused" | "stopped" }> {
  const res = await fetch(buildApiUrl(`/user-strategies/${userStrategyId}/state`, { env }), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action }),
  });
  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, `Failed to update strategy state (${res.status})`));
  }
  return res.json();
}
