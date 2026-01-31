import { useEffect, useMemo, useState } from "react";
import StrategyCard from "@/components/strategies/StrategyCard";
import StrategyDetailModal from "@/components/strategies/StrategyDetailModal";
import { getMyStrategies, getPublicStrategy } from "@/api/strategies";
import { useStrategies } from "@/hooks/useStrategies";
import type { MyStrategy, PublicStrategyDetail, PublicStrategyListItem } from "@/types/strategy";

export default function Strategies() {
  const { data: publicData, loading: publicLoading, error: publicError } = useStrategies();
  const [myData, setMyData] = useState<MyStrategy[] | null>(null);
  const [myLoading, setMyLoading] = useState(false);
  const [myError, setMyError] = useState<string | null>(null);
  const [myLoaded, setMyLoaded] = useState(false);
  const [scope, setScope] = useState<"public" | "private">("public");
  const [selected, setSelected] = useState<PublicStrategyListItem | null>(null);
  const [detail, setDetail] = useState<PublicStrategyDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const defaultSampleMetrics = useMemo(
    () => ({
      pnl_amount: 0,
      pnl_pct: 0,
      sharpe: 0,
      max_drawdown_pct: 0,
      win_rate_pct: 0
    }),
    []
  );
  const defaultTradeStats = useMemo(
    () => ({ trades_count: 0, avg_hold_hours: 0 }),
    []
  );
  const defaultPopularity = useMemo(
    () => ({ adds_count: 0, likes_count: 0, runs_count: 0 }),
    []
  );
  const isPublicScope = scope === "public";

  const mappedMyStrategies = useMemo<PublicStrategyListItem[]>(() => {
    if (!myData) return [];
    return myData.map((item) => ({
      public_strategy_id: item.my_strategy_id,
      name: item.name,
      one_liner: "",
      category: "My Strategy",
      tags: [],
      risk_level: "mid",
      version: item.public_version_snapshot || "1.0.0",
      author: { name: "You", type: "user" },
      sample_metrics: defaultSampleMetrics,
      sample_trade_stats: defaultTradeStats,
      popularity: defaultPopularity,
      supported_assets: [],
      supported_timeframes: [],
      updated_at: item.updated_at,
      created_at: item.created_at
    }));
  }, [myData, defaultSampleMetrics, defaultTradeStats, defaultPopularity]);

  const filteredData = useMemo(() => {
    if (isPublicScope) return publicData ?? [];
    return mappedMyStrategies;
  }, [isPublicScope, publicData, mappedMyStrategies]);

  useEffect(() => {
    if (isPublicScope) return;
    if (myLoaded) return;
    let isMounted = true;
    setMyLoading(true);
    setMyError(null);
    getMyStrategies()
      .then((result) => {
        if (!isMounted) return;
        setMyData(result.items ?? []);
        setMyLoaded(true);
      })
      .catch((err) => {
        if (!isMounted) return;
        setMyError(err instanceof Error ? err.message : "Failed to load my strategies");
      })
      .finally(() => {
        if (isMounted) setMyLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [isPublicScope, myLoaded]);

  useEffect(() => {
    if (!isPublicScope || !selected) {
      setDetail(null);
      setDetailError(null);
      setDetailLoading(false);
      return;
    }

    let isMounted = true;
    setDetailLoading(true);
    setDetailError(null);

    const load = async () => {
      try {
        const result = await getPublicStrategy(selected.public_strategy_id);
        if (isMounted) {
          setDetail(result);
        }
      } catch (err) {
        if (isMounted) {
          setDetailError(
            err instanceof Error ? err.message : "Failed to load strategy detail"
          );
        }
      } finally {
        if (isMounted) {
          setDetailLoading(false);
        }
      }
    };

    load();

    return () => {
      isMounted = false;
    };
  }, [selected]);

  useEffect(() => {
    if (!selected) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [selected]);

  useEffect(() => {
    if (!isPublicScope) {
      setSelected(null);
    }
  }, [isPublicScope]);

  if ((isPublicScope && publicLoading) || (!isPublicScope && myLoading)) {
    return <div className="text-sm text-gray-400">Loading strategies...</div>;
  }

  if ((isPublicScope && (publicError || !publicData)) || (!isPublicScope && myError)) {
    return (
      <div className="text-sm text-red-400">
        {isPublicScope ? publicError ?? "Failed to load strategies" : myError ?? "Failed to load my strategies"}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold mb-1">Strategies</h1>
          <p className="text-sm text-gray-400">
            Manage and monitor your trading strategies
          </p>
        </div>
        <div className="flex gap-5">
          <div className="flex items-center rounded-full border border-gray-800 bg-[#0d1117] p-1 text-xs">
            <button
              className={`px-3 py-1 rounded-full transition-colors ${
                scope === "public"
                  ? "bg-white text-black font-medium"
                  : "text-gray-400 hover:text-gray-200"
              }`}
              onClick={() => setScope("public")}
            >
              Public
            </button>
            <button
              className={`px-3 py-1 rounded-full transition-colors ${
                scope === "private"
                  ? "bg-white text-black font-medium"
                  : "text-gray-400 hover:text-gray-200"
              }`}
              onClick={() => setScope("private")}
            >
              My Strategies
            </button>
          </div>
          <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition-colors">
            + New Strategy
          </button>
        </div>
      </div>

      {filteredData.length === 0 ? (
        <div className="rounded-lg border border-gray-800 bg-[#0d1117] p-6 text-sm text-gray-400">
          {scope === "private"
            ? "No private strategies found."
            : "No strategies found."}
        </div>
      ) : (
        <div className="space-y-4">
          {filteredData.map((strategy) => (
            <StrategyCard
              key={strategy.public_strategy_id}
              strategy={strategy}
              onSelect={isPublicScope ? (item) => setSelected(item) : undefined}
            />
          ))}
        </div>
      )}

      <StrategyDetailModal
        open={Boolean(selected)}
        onClose={() => setSelected(null)}
        loading={detailLoading}
        error={detailError}
        detail={detail}
        fallbackTitle={selected?.name}
      />
    </div>
  );
}

