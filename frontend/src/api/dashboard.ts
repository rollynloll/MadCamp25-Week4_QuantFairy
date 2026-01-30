import type { DashboardData } from "@/types/dashboard";
import { activeStrategies, performanceData, recentTrades } from "@/data/dashboard.mock";

export async function getDashboard(): Promise<DashboardData> {
  // Replace this with real API call later.
  return {
    performance: performanceData,
    strategies: activeStrategies,
    trades: recentTrades,
  };
}
