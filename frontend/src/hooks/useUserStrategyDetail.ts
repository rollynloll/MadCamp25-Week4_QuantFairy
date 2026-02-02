// src/hooks/useUserStrategyDetail.ts
import { useEffect, useState } from "react";
import type { Env, UserStrategyDetailResponse } from "@/types/portfolio";
import { getUserStrategyDetail } from "@/api/userStrategies";

export function useUserStrategyDetail(env: Env, userStrategyId: string | null) {
  const [data, setData] = useState<UserStrategyDetailResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!userStrategyId) return;

    let isMounted = true;

    const load = async () => {
      setLoading(true);
      setError(null);

      try {
        const result = await getUserStrategyDetail(env, userStrategyId);
        if (isMounted) setData(result);
      } catch (err) {
        if (isMounted) setError(err instanceof Error ? err.message : "Failed to load strategy detail");
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    load();
    return () => {
      isMounted = false;
    };
  }, [env, userStrategyId]);

  return { data, loading, error };
}