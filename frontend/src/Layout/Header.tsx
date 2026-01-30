import { useEffect, useState } from "react";
import { AlertCircle, Play, Wifi } from "lucide-react";
import { useKillSwitch } from "@/hooks/useKillSwitch";

type TradeMode = "paper" | "live";

interface HeaderProps {
  mode: TradeMode;
  onModeChange: (mode: TradeMode) => void;
}

export default function Header({ mode, onModeChange }: HeaderProps) {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== "undefined" ? navigator.onLine : true
  );

  const { enabled, toggle } = useKillSwitch(false);

  const handleChange = async (next: "paper" | "live") => {
    if (next === "live") {
      const ok = window.confirm("Live 모드로 전환할까요?");
      if (!ok) return;
    }
    await onModeChange(next);
  }

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  return (
    <header className="h-16 bg-[#0d1117] border-b border-gray-800 flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 bg-[#0a0d14] rounded-lg p-1">
          <button
            onClick={() => onModeChange("paper")}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              mode === "paper"
                ? "bg-gray-700 text-white"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            Paper
          </button>
          <button
            onClick={() => onModeChange("live")}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              mode === "live"
                ? "bg-red-600/20 text-red-400 ring-1 ring-red-500/50"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            <span className="flex items-center gap-2">
              {mode === "live" && (
                <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              )}
              LIVE
            </span>
          </button>
        </div>

        {mode === "live" && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-red-600/10 border border-red-500/30 rounded text-xs text-red-400">
            <AlertCircle className="w-3 h-3" />
            <span>Live trading enabled</span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-6">
        <button
          type="button"
          aria-pressed={enabled}
          onClick={() => toggle(!enabled, "manual")}
          className={`group inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition-all ${
            enabled
              ? "bg-red-600/20 text-red-300 ring-1 ring-red-500/50 hover:bg-red-600/30"
              : "bg-amber-400/10 text-amber-200 ring-1 ring-amber-400/40 hover:bg-amber-400/20"
          }`}
        >
          <span
            className={`h-2 w-2 rounded-full ${
              enabled ? "bg-red-400 animate-pulse" : "bg-amber-300"
            }`}
          />
          {enabled ? "Kill Switch On" : "Enable Kill Switch"}
        </button>

        <div className="flex items-center gap-2 text-sm">
          <Wifi
            className={`w-4 h-4 ${
              isOnline ? "text-green-500" : "text-red-500"
            }`}
          />
          <span className="text-gray-400">
            {isOnline ? "Connected" : "Unconnected"}
          </span>
        </div>

        <div className="flex items-center gap-2 text-sm">
          <Play className="w-4 h-4 text-green-500" />
          <span className="text-gray-400">Running</span>
        </div>

        <div className="flex items-center gap-3 pl-6 border-l border-gray-800">
          <div className="text-right">
            <div className="text-xs text-gray-500">Account Balance</div>
            <div className="text-sm font-semibold">
              {mode === "paper" ? "$100,000.00" : "$50,245.87"}
            </div>
          </div>
          <div className="w-8 h-8 bg-blue-600/20 rounded-full flex items-center justify-center text-blue-400 text-sm font-medium">
            JD
          </div>
        </div>
      </div>
    </header>
  );
}
