import { useEffect, useState } from "react";
import { getTradingPositions } from "@/api/trading";
import type { TradingPositionItem } from "@/types/trading";

export function useTradingPositions() {
  const [items, setItems] = useState<TradingPositionItem[]>([]);
  const [asOf, setAsOf] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await getTradingPositions();
        if (cancelled) return;
        setItems(res.items ?? []);
        setAsOf(res.as_of ?? null);
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : "Failed to load positions");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();

    return () => {
      cancelled = true;
    };
  }, []);

  return { items, asOf, loading, error };
}