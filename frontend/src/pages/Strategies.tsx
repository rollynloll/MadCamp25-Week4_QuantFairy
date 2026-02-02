import { useEffect, useMemo, useState } from "react";
import { Check, Minus } from "lucide-react";
import StrategyCard from "@/components/strategies/StrategyCard";
import StrategyDetailModal from "@/components/strategies/StrategyDetailModal";
import {
  addPublicStrategyToMy,
  deleteMyStrategy,
  getMyStrategies,
  getPublicStrategy
} from "@/api/strategies";
import { useStrategies } from "@/hooks/useStrategies";
import type {
  MyStrategy,
  PublicStrategyDetail,
  PublicStrategyListItem
} from "@/types/strategy";

export default function Strategies() {
  const { data, loading, error } = useStrategies();
  const [scope, setScope] = useState<"public" | "private">("public");
  const [selected, setSelected] = useState<PublicStrategyListItem | null>(null);
  const [detail, setDetail] = useState<PublicStrategyDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [myStrategies, setMyStrategies] = useState<MyStrategy[]>([]);
  const [myLoading, setMyLoading] = useState(false);
  const [myError, setMyError] = useState<string | null>(null);
  const [addingIds, setAddingIds] = useState<Set<string>>(new Set());
  const publicStrategyById = useMemo(() => {
    return new Map((data ?? []).map((item) => [item.public_strategy_id, item]));
  }, [data]);

  const myFromPublic = useMemo(() => {
    return myStrategies
      .filter((item) => Boolean(item.source_public_strategy_id))
      .map((myItem) => publicStrategyById.get(myItem.source_public_strategy_id))
      .filter(Boolean) as PublicStrategyListItem[];
  }, [myStrategies, publicStrategyById]);

  const myCustom = useMemo(() => {
    return myStrategies.filter((item) => !item.source_public_strategy_id);
  }, [myStrategies]);

  const myStrategyIdByPublicId = useMemo(() => {
    const map = new Map<string, string>();
    myStrategies.forEach((item) => {
      if (!map.has(item.source_public_strategy_id)) {
        map.set(item.source_public_strategy_id, item.my_strategy_id);
      }
    });
    return map;
  }, [myStrategies]);

  const handleAddToMy = (strategy: PublicStrategyListItem) => {
    if (myStrategyIdByPublicId.has(strategy.public_strategy_id)) {
      return;
    }
    setMyError(null);
    setAddingIds((prev) => new Set(prev).add(strategy.public_strategy_id));
    getPublicStrategy(strategy.public_strategy_id)
      .then((detailResult) =>
        addPublicStrategyToMy(strategy.public_strategy_id, {
          name: strategy.name,
          params: detailResult.default_params ?? {}
        })
      )
      .then((created) => {
        setMyStrategies((prev) => {
          if (prev.some((item) => item.my_strategy_id === created.my_strategy_id)) {
            return prev;
          }
          return [created, ...prev];
        });
      })
      .catch((err) => {
        setMyError(err instanceof Error ? err.message : "Failed to add strategy");
      })
      .finally(() => {
        setAddingIds((prev) => {
          const next = new Set(prev);
          next.delete(strategy.public_strategy_id);
          return next;
        });
      });
  };

  const handleRemoveFromMy = (strategy: PublicStrategyListItem) => {
    const myId = myStrategyIdByPublicId.get(strategy.public_strategy_id);
    if (!myId) return;
    if (!window.confirm("Remove this strategy from My Strategies?")) return;
    setMyError(null);
    deleteMyStrategy(myId)
      .then(() => {
        setMyStrategies((prev) =>
          prev.filter((item) => item.my_strategy_id !== myId)
        );
      })
      .catch((err) => {
        setMyError(
          err instanceof Error ? err.message : "Failed to remove strategy"
        );
      });
  };

  const handleRemoveCustom = (myStrategyId: string) => {
    if (!window.confirm("Remove this custom strategy?")) return;
    setMyError(null);
    deleteMyStrategy(myStrategyId)
      .then(() => {
        setMyStrategies((prev) =>
          prev.filter((item) => item.my_strategy_id !== myStrategyId)
        );
      })
      .catch((err) => {
        setMyError(
          err instanceof Error ? err.message : "Failed to remove strategy"
        );
      });
  };

  useEffect(() => {
    let isMounted = true;
    setMyLoading(true);
    setMyError(null);

    getMyStrategies()
      .then((result) => {
        if (isMounted) {
          setMyStrategies(result.items);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setMyError(
            err instanceof Error ? err.message : "Failed to load my strategies"
          );
        }
      })
      .finally(() => {
        if (isMounted) {
          setMyLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (!selected) {
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

  if (loading) {
    return <div className="text-sm text-gray-400">Loading strategies...</div>;
  }

  if (error || !data) {
    return (
      <div className="text-sm text-red-400">
        {error ?? "Failed to load strategies"}
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

      {scope === "private" && myLoading ? (
        <div className="text-sm text-gray-400">Loading my strategies...</div>
      ) : scope === "private" && myError ? (
        <div className="text-sm text-red-400">{myError}</div>
      ) : scope === "private" && myFromPublic.length === 0 && myCustom.length === 0 ? (
        <div className="rounded-lg border border-gray-800 bg-[#0d1117] p-6 text-sm text-gray-400">
          No private strategies found.
        </div>
      ) : (
        <div className="space-y-6">
          {scope === "public" && (
            <div className="space-y-4">
              {(data ?? []).map((strategy) => (
                <div
                  key={strategy.public_strategy_id}
                  className="relative"
                >
                  {(() => {
                    const isAdded = myStrategyIdByPublicId.has(strategy.public_strategy_id);
                    const isAdding = addingIds.has(strategy.public_strategy_id);
                    return (
                      <div
                        className={
                          isAdded || isAdding
                            ? "rounded-lg ring-1 ring-green-500/40 bg-green-500/5"
                            : ""
                        }
                      >
                        <StrategyCard
                          strategy={strategy}
                          onSelect={(item) => setSelected(item)}
                          onAdd={isAdded || isAdding ? undefined : handleAddToMy}
                        />
                        {(isAdding || isAdded) && (
                          <div className="absolute top-4 right-4 flex items-center gap-1 rounded-full bg-green-600/20 px-2 py-1 text-xs text-green-300">
                            <Check className="w-3 h-3" />
                            {isAdding ? "Adding" : "Added"}
                          </div>
                        )}
                      </div>
                    );
                  })()}
                </div>
              ))}
            </div>
          )}

          {scope === "private" && (
            <>
              <div className="space-y-3">
                <div className="text-xs uppercase tracking-wide text-gray-500">
                  From Public Strategies
                </div>
                {myFromPublic.length === 0 ? (
                  <div className="text-sm text-gray-400">
                    No strategies added from Public.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {myFromPublic.map((strategy) => (
                      <StrategyCard
                        key={strategy.public_strategy_id}
                        strategy={strategy}
                        onSelect={(item) => setSelected(item)}
                        onRemove={handleRemoveFromMy}
                      />
                    ))}
                  </div>
                )}
              </div>

              <div className="space-y-3">
                <div className="text-xs uppercase tracking-wide text-gray-500">
                  Custom Strategies
                </div>
                {myCustom.length === 0 ? (
                  <div className="text-sm text-gray-400">
                    No custom strategies yet.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {myCustom.map((strategy) => (
                      <div
                        key={strategy.my_strategy_id}
                        className="bg-[#0d1117] border border-gray-800 rounded-lg p-6"
                      >
                        <div className="flex items-start justify-between gap-6 mb-3">
                          <div>
                            <h3 className="text-lg font-semibold">
                              {strategy.name}
                            </h3>
                            {strategy.note && (
                              <p className="text-sm text-gray-400 mt-1">
                                {strategy.note}
                              </p>
                            )}
                          </div>
                          <button
                            onClick={() => handleRemoveCustom(strategy.my_strategy_id)}
                            className="p-1.5 hover:bg-gray-800 rounded transition-colors"
                            title="Remove"
                            type="button"
                          >
                            <Minus size={16} />
                          </button>
                        </div>
                        <div className="text-xs text-gray-500">
                          Created: {new Date(strategy.created_at).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
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
