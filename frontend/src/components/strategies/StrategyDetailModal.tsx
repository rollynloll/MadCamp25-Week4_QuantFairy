import type { PublicStrategyDetail } from "@/types/strategy";

interface StrategyDetailModalProps {
  open: boolean;
  onClose: () => void;
  loading: boolean;
  error: string | null;
  detail: PublicStrategyDetail | null;
  fallbackTitle?: string | null;
}

export default function StrategyDetailModal({
  open,
  onClose,
  loading,
  error,
  detail,
  fallbackTitle
}: StrategyDetailModalProps) {
  if (!open) return null;

  const title = detail?.name ?? fallbackTitle ?? "Strategy detail";

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/70 p-6"
      onClick={onClose}
    >
      <div
        className="w-full max-w-3xl rounded-xl border border-gray-800 bg-[#0d1117] shadow-xl"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-gray-800 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold">{title}</h2>
            {detail?.one_liner && (
              <p className="text-xs text-gray-400 mt-1">{detail.one_liner}</p>
            )}
          </div>
          <button
            className="text-sm text-gray-400 hover:text-gray-200"
            onClick={onClose}
          >
            Close
          </button>
        </div>

        <div className="max-h-[70vh] overflow-y-auto px-6 py-5 space-y-5 text-sm">
          {loading && (
            <div className="text-gray-400">Loading strategy detail...</div>
          )}

          {error && (
            <div className="text-red-400">{error}</div>
          )}

          {!loading && !error && detail && (
            <>
              <section className="space-y-3">
                <h3 className="text-sm font-semibold">Overview</h3>
                <div className="grid gap-3 sm:grid-cols-2 text-gray-300">
                  <div>
                    <div className="text-xs text-gray-500">Author</div>
                    <div>{detail.author?.name ?? "Unknown"}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Author Type</div>
                    <div>{detail.author?.type ?? "N/A"}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Category</div>
                    <div>{detail.category}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Risk Level</div>
                    <div>{detail.risk_level}</div>
                  </div>
                  {/* <div>
                    <div className="text-xs text-gray-500">Version</div>
                    <div>{detail.version}</div>
                  </div> */}
                  {/* <div>
                    <div className="text-xs text-gray-500">Updated</div>
                    <div>{new Date(detail.updated_at).toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Created</div>
                    <div>{new Date(detail.created_at).toLocaleString()}</div>
                  </div> */}
                </div>
                {detail.tags?.length > 0 && (
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Tags</div>
                    <div className="flex flex-wrap gap-2">
                      {detail.tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 bg-gray-800 text-gray-400 text-xs rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </section>

              <section>
                <h3 className="text-sm font-semibold mb-2 mt-10">Description</h3>
                <p className="text-gray-300 whitespace-pre-line">
                  {detail.full_description}
                </p>
                {detail.thesis && (
                  <p className="text-gray-400 mt-3 whitespace-pre-line">
                    {detail.thesis}
                  </p>
                )}
              </section>

              <section>
                <h3 className="text-sm font-semibold mb-2 mt-10">Coverage</h3>
                <div className="grid gap-3 sm:grid-cols-2 text-gray-300">
                  <div>
                    <div className="text-xs text-gray-500">Assets</div>
                    <div>
                      {detail.supported_assets?.length
                        ? detail.supported_assets.join(", ")
                        : "N/A"}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Timeframes</div>
                    <div>
                      {detail.supported_timeframes?.length
                        ? detail.supported_timeframes.join(", ")
                        : "N/A"}
                    </div>
                  </div>
                </div>
              </section>

              <section>
                <h3 className="text-sm font-semibold mb-2 mt-10">Popularity</h3>
                <div className="grid gap-3 sm:grid-cols-3 text-gray-300">
                  <div>
                    <div className="text-xs text-gray-500">Adds</div>
                    <div>{detail.popularity?.adds_count ?? 0}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Likes</div>
                    <div>{detail.popularity?.likes_count ?? 0}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Runs</div>
                    <div>{detail.popularity?.runs_count ?? 0}</div>
                  </div>
                </div>
              </section>

              <section>
                <h3 className="text-sm font-semibold mb-2 mt-10">Sample Metrics</h3>
                <div className="grid gap-3 sm:grid-cols-2 text-gray-300">
                  <div>
                    <div className="text-xs text-gray-500">P&L Amount</div>
                    <div>{detail.sample_metrics?.pnl_amount ?? 0}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">P&L %</div>
                    <div>{detail.sample_metrics?.pnl_pct ?? 0}%</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Sharpe</div>
                    <div>{detail.sample_metrics?.sharpe ?? 0}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Max DD %</div>
                    <div>{detail.sample_metrics?.max_drawdown_pct ?? 0}%</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Win Rate %</div>
                    <div>{detail.sample_metrics?.win_rate_pct ?? 0}%</div>
                  </div>
                </div>
              </section>

              <section>
                <h3 className="text-sm font-semibold mb-2 mt-10">Sample Trade Stats</h3>
                <div className="grid gap-3 sm:grid-cols-2 text-gray-300">
                  <div>
                    <div className="text-xs text-gray-500">Trades</div>
                    <div>{detail.sample_trade_stats?.trades_count ?? 0}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Avg Hold (h)</div>
                    <div>{detail.sample_trade_stats?.avg_hold_hours ?? 0}</div>
                  </div>
                </div>
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
