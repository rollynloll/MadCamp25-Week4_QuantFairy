import { setTradingMode } from "@/api/dashboard";
import type { ModeEnvironment } from "@/types/dashboard";
import { useState } from "react";

export function useTradingMode(initial: ModeEnvironment) {
  const [mode, setMode] = useState<ModeEnvironment>(initial);
  const [loading, setLoading] = useState(false);

  const changeMode = async(next: ModeEnvironment) => {
    setLoading(true);
    try {
      const res = await setTradingMode(next);
      setMode(res.environment);
    } finally {
      setLoading(false);
    }
  };

  return { mode, loading, changeMode };
}