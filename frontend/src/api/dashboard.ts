import type { BotState, DashboardResponse, ModeEnvironment, Range } from "@/types/dashboard";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();

const buildUrl = (path: string, params?: Record<string, string>) => {
  if (!API_BASE_URL) {
    if (!params) return path;
    const qs = new URLSearchParams(params);
    return `${path}?${qs.toString()}`;
  }

  const url = new URL(path, API_BASE_URL);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.set(key, value);
    });
  }
  return url.toString();
};

// 대시보드 데이터 저장
export async function getDashboard(range: Range = "1M"): Promise<DashboardResponse> {
  const res = await fetch(buildUrl("/api/v1/dashboard", { range }), {
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message =
      body?.error?.message ?? `Failed to load dashboard (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}

// paper / live 모드 갱신
export async function setTradingMode(environment: ModeEnvironment) {
  const res = await fetch(buildUrl("/api/v1/trading/mode"), {
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

// kill-switch enabled 갱신
export async function setKillSwitch(enabled: boolean, reason: string) {
  const res = await fetch(buildUrl("/api/v1/trading/kill-switch"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled, reason }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message =
      body?.error?.message ?? `Failed to set kill switch (${res.status})`;
    throw new Error(message);
  }

  return res.json() as Promise<{ enabled: boolean }>;
}

// bot start
export async function startBot() {
  const res = await fetch(buildUrl("/api/v1/bot/start"), { method: "POST" });
  if (!res.ok) throw new Error("Failed to start bot");
  return res.json() as Promise<{ state: BotState }>;
}

// bot stop
export async function stopBot() {
  const res = await fetch(buildUrl("/api/v1/bot/stop"), { method: "POST" });
  if (!res.ok) throw new Error("Failed to stop bot");
  return res.json() as Promise<{ state: BotState }>;
}

// bot run-now
export async function runBotNow() {
  const res = await fetch(buildUrl("/api/v1/bot/run-now"), { method: "POST" });
  if (!res.ok) throw new Error("Failed to run bot");
  return res.json() as Promise<{ run_id: string; state: "queued" }>;
}
