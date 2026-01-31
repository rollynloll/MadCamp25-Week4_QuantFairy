import { useEffect, useState } from "react";
import type { PublicStrategyListItem } from "@/types/strategy";
import { getPublicStrategies } from "@/api/strategies";

interface UseStrategiesResult {
  data: PublicStrategyListItem[] | null;
  nextCursor: string | null;
  loading: boolean;
  error: string | null;
}

export function useStrategies(): UseStrategiesResult {
  const [data, setData] = useState<PublicStrategyListItem[] | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      try {
        const result = await getPublicStrategies();
        if (isMounted) {
          setData(result.items);
          setNextCursor(result.next_cursor);
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

  return { data, nextCursor, loading, error };
}