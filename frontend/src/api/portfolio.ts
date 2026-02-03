// src/api/portfolio.ts
import { buildApiUrl } from "@/api/base";
import type {
  Env,
  Range,
  PortfolioSummaryResponse,
  PortfolioOverviewResponse,
  PortfolioPerformanceResponse,
  PortfolioDrawdownResponse,
  PortfolioKpiResponse,
  PortfolioPositionsResponse,
  PortfolioAllocationResponse,
  PortfolioActivityResponse,
  PortfolioAttributionResponse,
  PortfolioRebalanceRequest,
  PortfolioRebalanceResponse,
} from "@/types/portfolio";

async function parseErrorMessage(res: Response, fallback: string) {
  const body = await res.json().catch(() => null);
  return body?.error?.message ?? fallback;
}

// 0.1 summary
export async function getPortfolioSummary(env: Env): Promise<PortfolioSummaryResponse> {
  const res = await fetch(buildApiUrl("/portfolio/summary", { env }), {
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, `Failed to load portfolio summary (${res.status})`));
  }
  return res.json();
}

// 0.2 overview
export async function getPortfolioOverview(env: Env): Promise<PortfolioOverviewResponse> {
  const res = await fetch(buildApiUrl("/portfolio/overview", { env }), {
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, `Failed to load portfolio overview (${res.status})`));
  }
  return res.json();
}

// 1.1 performance
export async function getPortfolioPerformance(params: {
  env: Env;
  range: Range;
  benchmark?: string;
}): Promise<PortfolioPerformanceResponse> {
  const res = await fetch(buildApiUrl("/portfolio/performance", params), {
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, `Failed to load performance (${res.status})`));
  }
  return res.json();
}

// 1.2 drawdown
export async function getPortfolioDrawdown(env: Env, range: Range): Promise<PortfolioDrawdownResponse> {
  const res = await fetch(buildApiUrl("/portfolio/drawdown", { env, range }), {
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, `Failed to load drawdown (${res.status})`));
  }
  return res.json();
}

// 1.3 kpi
export async function getPortfolioKpi(env: Env, range: Range): Promise<PortfolioKpiResponse> {
  const res = await fetch(buildApiUrl("/portfolio/kpi", { env, range }), {
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, `Failed to load kpi (${res.status})`));
  }
  return res.json();
}

// 2.1 positions
export async function getPortfolioPositions(env: Env): Promise<PortfolioPositionsResponse> {
  const res = await fetch(buildApiUrl("/portfolio/positions", { env }), {
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, `Failed to load positions (${res.status})`));
  }
  return res.json();
}

// 2.2 allocation
export async function getPortfolioAllocation(env: Env): Promise<PortfolioAllocationResponse> {
  const res = await fetch(buildApiUrl("/portfolio/allocation", { env }), {
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, `Failed to load allocation (${res.status})`));
  }
  return res.json();
}

// 2.3 attribution
export async function getPortfolioAttribution(params: {
  env: Env;
  by: "strategy" | "sector";
  range?: Range;
}): Promise<PortfolioAttributionResponse> {
  const res = await fetch(buildApiUrl("/portfolio/attribution", params), {
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, `Failed to load attribution (${res.status})`));
  }
  return res.json();
}

// 4.1 activity
export async function getPortfolioActivity(params: {
  env: Env;
  types?: string;
  limit?: number;
  cursor?: string;
}): Promise<PortfolioActivityResponse> {
  const res = await fetch(buildApiUrl("/portfolio/activity", params), {
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, `Failed to load activity (${res.status})`));
  }
  return res.json();
}

// 5.1 rebalance
export async function rebalancePortfolio(
  params: PortfolioRebalanceRequest & { env: Env }
): Promise<PortfolioRebalanceResponse> {
  const { env, ...body } = params;
  const res = await fetch(buildApiUrl("/portfolio/rebalance", { env }), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, `Failed to rebalance (${res.status})`));
  }
  return res.json();
}
