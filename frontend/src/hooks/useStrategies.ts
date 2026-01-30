import { useEffect, useState } from "react";
import type { Strategy } from "@/types/strategy";
import { getStrategies } from "@/api/strategies";

interface UseStrategiesResult {
  data: Strategy[] | null;
  loading: boolean;
  error: string | null;
}

export function useStrategies(): UseStrategiesResult {
  const [data, setData] = useState<Strategy[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      try {
        const result = await getStrategies();
        if (isMounted) {
          setData(result);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load strategies");
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
  }, []);

  return { data, loading, error };
}
