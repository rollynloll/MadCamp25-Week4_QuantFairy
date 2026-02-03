
import { useEffect, useState } from "react";
import { getMyStrategies } from "@/api/strategies";
import type { MyStrategy } from "@/types/strategy";

export function useMyStrategies() {
  const [myStrategies, setMyStrategies] = useState<MyStrategy[]>([]);

  useEffect(() => {
    let cancelled = false;

    const loadMyStrategies = async () => {
      try {
        const res = await getMyStrategies();
        if (!cancelled) {
          setMyStrategies(res.items ?? []);
        }
      } catch {
        if (!cancelled) {
          setMyStrategies([]);
        }
      }
    };

    loadMyStrategies();

    return () => {
      cancelled = true;
    };
  }, []);

  return { myStrategies };
}
