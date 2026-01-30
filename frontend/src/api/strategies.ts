import type { Strategy } from "@/types/strategy";
import { strategies } from "@/data/strategies.mock";

export async function getStrategies(): Promise<Strategy[]> {
  // Replace with real API call later.
  return strategies;
}
