import { useEffect, useState } from "react";
import type { BotState } from "@/types/dashboard";
import { runBotNow, startBot, stopBot } from "@/api/dashboard";

export function useBotControl(initial: BotState) {
  const [state, setState] = useState<BotState>(initial);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setState(initial);
  }, [initial]);

  const start = async () => {
    setLoading(true);
    setState("running");
    try {
      const res = await startBot();
      setState(res.state);
    } finally {
      setLoading(false);
    }
  };

  const stop = async () => {
    setLoading(true);
    setState("stopped");
    try {
      const res = await stopBot();
      setState(res.state);
    } finally {
      setLoading(false);
    }
  };

  const runNow = async () => {
    setLoading(true);
    setState("queued");
    try {
      const res = await runBotNow();
      setState(res.state);
    } finally {
      setLoading(false);
    }
  };


  return { state, loading, start, stop, runNow };
}