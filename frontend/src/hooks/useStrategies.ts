import { useEffect, useState } from "react";
import type { PublicStrategyListItem } from "@/types/strategy";
import { getPublicStrategies } from "@/api/strategies";

interface UseStrategiesResult {
  data: PublicStrategyListItem[] | null;
  nextCursor: string | null;
  loading: boolean;
  error: string | null;
}

let cachedPublicStrategies: PublicStrategyListItem[] | null = null;
let cachedNextCursor: string | null = null;

export function useStrategies(): UseStrategiesResult {
  const [data, setData] = useState<PublicStrategyListItem[] | null>(cachedPublicStrategies);
  const [nextCursor, setNextCursor] = useState<string | null>(cachedNextCursor);
  const [loading, setLoading] = useState(!cachedPublicStrategies);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (cachedPublicStrategies) {
      return;
    }
    let isMounted = true;

    const load = async () => {
      try {
        const result = await getPublicStrategies();
        if (isMounted) {
          cachedPublicStrategies = result.items;
          cachedNextCursor = result.next_cursor ?? null;
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
