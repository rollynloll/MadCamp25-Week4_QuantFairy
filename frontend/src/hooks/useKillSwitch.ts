import { useState } from "react";
import { setKillSwitch } from "@/api/dashboard";

export function useKillSwitch(initial: boolean) {
  const [enabled, setEnabled] = useState(initial);
  const [loading, setLoading] = useState(false);

  const toggle = async (next: boolean, reason: string) => {
    setLoading(true);
    try {
      const res = await setKillSwitch(next, reason);
      setEnabled(res.enabled);
    } finally {
      setLoading(false);
    }
  };

  return { enabled, loading, toggle };
}