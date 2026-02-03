import type { PublicStrategyDetail } from "@/types/strategy";
import { useLanguage } from "@/contexts/LanguageContext";

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
  const { tr } = useLanguage();

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
            {tr("Close", "닫기")}
          </button>
        </div>

        <div className="max-h-[70vh] overflow-y-auto px-6 py-5 space-y-5 text-sm">
          {loading && (
            <div className="text-gray-400">{tr("Loading strategy detail...", "전략 상세 불러오는 중...")}</div>
          )}

          {error && (
            <div className="text-red-400">{error}</div>
          )}

          {!loading && !error && detail && (
            <>
              <section className="space-y-3">
                <h3 className="text-sm font-semibold">{tr("Overview", "개요")}</h3>
                <div className="grid gap-3 sm:grid-cols-2 text-gray-300">
                  <div>
                    <div className="text-xs text-gray-500">{tr("Author", "작성자")}</div>
                    <div>{detail.author?.name ?? tr("Unknown", "알 수 없음")}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">{tr("Author Type", "작성자 유형")}</div>
                    <div>{detail.author?.type ?? tr("N/A", "없음")}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">{tr("Category", "카테고리")}</div>
                    <div>{detail.category}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">{tr("Risk Level", "리스크 수준")}</div>
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
                    <div className="text-xs text-gray-500 mb-1">{tr("Tags", "태그")}</div>
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
                <h3 className="text-sm font-semibold mb-2 mt-10">{tr("Description", "설명")}</h3>
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
                <h3 className="text-sm font-semibold mb-2 mt-10">{tr("Coverage", "커버리지")}</h3>
                <div className="grid gap-3 sm:grid-cols-2 text-gray-300">
                  <div>
                    <div className="text-xs text-gray-500">{tr("Assets", "자산")}</div>
                    <div>
                      {detail.supported_assets?.length
                        ? detail.supported_assets.join(", ")
                        : tr("N/A", "없음")}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">{tr("Timeframes", "타임프레임")}</div>
                    <div>
                      {detail.supported_timeframes?.length
                        ? detail.supported_timeframes.join(", ")
                        : tr("N/A", "없음")}
                    </div>
                  </div>
                </div>
              </section>

              <section>
                <h3 className="text-sm font-semibold mb-2 mt-10">{tr("Popularity", "인기도")}</h3>
                <div className="grid gap-3 sm:grid-cols-3 text-gray-300">
                  <div>
                    <div className="text-xs text-gray-500">{tr("Adds", "추가")}</div>
                    <div>{detail.popularity?.adds_count ?? 0}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">{tr("Likes", "좋아요")}</div>
                    <div>{detail.popularity?.likes_count ?? 0}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">{tr("Runs", "실행")}</div>
                    <div>{detail.popularity?.runs_count ?? 0}</div>
                  </div>
                </div>
              </section>

              <section>
                <h3 className="text-sm font-semibold mb-2 mt-10">{tr("Sample Metrics", "샘플 지표")}</h3>
                <div className="grid gap-3 sm:grid-cols-2 text-gray-300">
                  <div>
                    <div className="text-xs text-gray-500">{tr("P&L Amount", "손익 금액")}</div>
                    <div>{detail.sample_metrics?.pnl_amount ?? 0}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">{tr("P&L %", "손익 %")}</div>
                    <div>{detail.sample_metrics?.pnl_pct ?? 0}%</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">{tr("Sharpe", "샤프")}</div>
                    <div>{detail.sample_metrics?.sharpe ?? 0}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">{tr("Max DD %", "최대 낙폭 %")}</div>
                    <div>{detail.sample_metrics?.max_drawdown_pct ?? 0}%</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">{tr("Win Rate %", "승률 %")}</div>
                    <div>{detail.sample_metrics?.win_rate_pct ?? 0}%</div>
                  </div>
                </div>
              </section>

              <section>
                <h3 className="text-sm font-semibold mb-2 mt-10">{tr("Sample Trade Stats", "샘플 거래 통계")}</h3>
                <div className="grid gap-3 sm:grid-cols-2 text-gray-300">
                  <div>
                    <div className="text-xs text-gray-500">{tr("Trades", "거래 수")}</div>
                    <div>{detail.sample_trade_stats?.trades_count ?? 0}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">{tr("Avg Hold (h)", "평균 보유 (h)")}</div>
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
