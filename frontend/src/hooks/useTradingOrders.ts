import { useCallback, useEffect, useState } from "react";
import { getTradingOrders, type OrderScope } from "@/api/trading";
import type { TradingOrder } from "@/types/trading";

export function useTradingOrders(scope: OrderScope) {
  const [items, setItems] = useState<TradingOrder[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getTradingOrders({ scope, limit: 50 });
      setItems(res.items ?? []);
      setNextCursor(res.next_cursor ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load orders");
    } finally {
      setLoading(false);
    }
  }, [scope]);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  return { items, loading, error, nextCursor, refetch: fetchOrders };
}
