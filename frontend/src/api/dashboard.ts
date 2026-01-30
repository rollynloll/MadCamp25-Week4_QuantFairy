import type { DashboardResponse, ModeEnvironment, Range } from "@/types/dashboard";

export async function getDashboard(range: Range = "1M"): Promise<DashboardResponse> {
  const res = await fetch(`/api/v1/dashboard?range=${encodeURIComponent(range)}`, {
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!res.ok) {
    // 공통 에러 포맷 처리
    const body = await res.json().catch(() => null);
    const message =
      body?.error?.message ?? `Failed to load dashboard (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}

export async function setTradingMode(environment: ModeEnvironment) {
  const res = await fetch("/api/v1/trading/mode", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ environment }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.error?.message ?? `Failed to set mode (${res.status})`;
    throw new Error(message);
  }

  return res.json() as Promise<{ environment: ModeEnvironment }>;
}
