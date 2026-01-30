import { useEffect, useState } from "react";
import { getDashboard } from "@/api/dashboard";
import type { DashboardResponse, Range } from "@/types/dashboard";

interface UseDashboardResult {
  data: DashboardResponse | null;
  loading: boolean;
  error: string | null;
}

export function useDashboard(range: Range): UseDashboardResult {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      setLoading(true);
      setError(null);

      try {
        const result = await getDashboard(range);
        if (isMounted) {
          setData(result);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load dashboard");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    load();

    return () => {
      isMounted = false;
    };
  }, [range]);

  return { data, loading, error };
}
