import type { Env, UserStrategyListItem } from "@/types/portfolio";
import { useUserStrategyDetail } from "@/hooks/useUserStrategyDetail";
import { X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useLanguage } from "@/contexts/LanguageContext";

interface StrategyEditProps {
  open: boolean;
  env: Env;
  strategyId: string | null;
  strategies: UserStrategyListItem[];
  onClose: () => void;
  onSave: (strategyId: string, body: { name?: string; params?: Record<string, any>; risk_limits?: Record<string, any> }) => void;
}

export default function StrategyEditDrawer({
  open,
  env,
  strategyId,
  strategies,
  onClose,
  onSave,
}: StrategyEditProps) {
  const { tr } = useLanguage();
  const { data, loading, error } = useUserStrategyDetail(env, open ? strategyId : null);

  const listItem = useMemo(
    () => (strategyId ? strategies.find((s) => s.user_strategy_id === strategyId) : undefined),
    [strategies, strategyId]
  );

  // 로컬 폼 상태
  const [name, setName] = useState("");
  const [params, setParams] = useState<Record<string, any>>({});
  const [risk, setRisk] = useState<Record<string, any>>({});

  // detail 로드되면 폼 초기화
  useEffect(() => {
    if (!data) return;
    setName(data.name ?? "");
    setParams(data.params ?? {});
    setRisk(data.risk_limits ?? {});
  }, [data]);

  if (!open || strategyId == null) return null;

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex justify-end">
      <div className="w-[500px] bg-[#0a0d14] border-l border-gray-800 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
          <h3 className="font-semibold">
            {tr("Edit Strategy", "전략 편집")}: {data?.name ?? listItem?.name ?? tr("Unknown", "알 수 없음")}
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-800 rounded transition-colors" type="button">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4 space-y-6">
          {loading && <div className="text-sm text-gray-500">{tr("Loading...", "불러오는 중...")}</div>}
          {error && <div className="text-sm text-red-400">{error}</div>}

          {!loading && !error && (
            <>
              {/* Summary */}
              <div>
                <h4 className="text-sm font-semibold mb-3 text-gray-400">{tr("Summary", "요약")}</h4>
                <div className="space-y-2 text-sm">
                  <Row label={tr("State", "상태")} value={(data?.state ?? listItem?.state ?? "unknown").toString().toUpperCase()} />
                  <Row label={tr("Positions", "포지션")} value={String(listItem?.positions_count ?? "-")} />
                  <Row
                    label={tr("P&L (Today)", "오늘 손익")}
                    value={
                      listItem?.today_pnl
                        ? `${listItem.today_pnl.value >= 0 ? "+" : ""}$${listItem.today_pnl.value.toFixed(2)}`
                        : "-"
                    }
                    valueClassName={listItem?.today_pnl && listItem.today_pnl.value >= 0 ? "text-green-500" : "text-red-500"}
                  />
                </div>
              </div>

              {/* Name */}
              <div>
                <h4 className="text-sm font-semibold mb-3 text-gray-400">{tr("General", "일반")}</h4>
                <Field label={tr("Name", "이름")}>
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full bg-[#0d1117] border border-gray-800 rounded px-3 py-2 text-sm"
                  />
                </Field>
              </div>

              {/* Parameters */}
              <div>
                <h4 className="text-sm font-semibold mb-3 text-gray-400">{tr("Parameters", "파라미터")}</h4>

                {data?.public_strategy?.param_schema ? (
                  <div className="space-y-4">
                    {Object.entries(data.public_strategy.param_schema).map(([key, schema]) => (
                      <Field key={key} label={key}>
                        <input
                          type="number"
                          value={params[key] ?? schema.default ?? ""}
                          onChange={(e) => setParams((prev) => ({ ...prev, [key]: Number(e.target.value) }))}
                          className="w-full bg-[#0d1117] border border-gray-800 rounded px-3 py-2 text-sm"
                        />
                        {(schema.min !== undefined || schema.max !== undefined) && (
                          <div className="text-xs text-gray-500 mt-1">
                            {schema.min !== undefined ? `min ${schema.min}` : ""}{" "}
                            {schema.max !== undefined ? `max ${schema.max}` : ""}
                          </div>
                        )}
                      </Field>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-gray-500">{tr("No param schema", "파라미터 스키마 없음")}</div>
                )}
              </div>

              {/* Risk Limits */}
              <div>
                <h4 className="text-sm font-semibold mb-3 text-gray-400">{tr("Risk Limits", "리스크 제한")}</h4>
                <div className="space-y-4">
                  <Field label="max_weight_per_asset">
                    <input
                      type="number"
                      step="0.01"
                      value={risk.max_weight_per_asset ?? ""}
                      onChange={(e) => setRisk((prev) => ({ ...prev, max_weight_per_asset: Number(e.target.value) }))}
                      className="w-full bg-[#0d1117] border border-gray-800 rounded px-3 py-2 text-sm"
                    />
                  </Field>

                  <Field label="cash_buffer">
                    <input
                      type="number"
                      step="0.01"
                      value={risk.cash_buffer ?? ""}
                      onChange={(e) => setRisk((prev) => ({ ...prev, cash_buffer: Number(e.target.value) }))}
                      className="w-full bg-[#0d1117] border border-gray-800 rounded px-3 py-2 text-sm"
                    />
                  </Field>

                  <Field label="max_turnover_pct">
                    <input
                      type="number"
                      step="1"
                      value={risk.max_turnover_pct ?? ""}
                      onChange={(e) => setRisk((prev) => ({ ...prev, max_turnover_pct: Number(e.target.value) }))}
                      className="w-full bg-[#0d1117] border border-gray-800 rounded px-3 py-2 text-sm"
                    />
                  </Field>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-800 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm font-medium transition-colors"
            type="button"
          >
            {tr("Cancel", "취소")}
          </button>
          <button
            onClick={() => onSave(strategyId, { name, params, risk_limits: risk })}
            className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition-colors"
            type="button"
            disabled={loading}
          >
            {tr("Save", "저장")}
          </button>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value, valueClassName }: { label: string; value: string; valueClassName?: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-500">{label}</span>
      <span className={`font-mono ${valueClassName ?? ""}`}>{value}</span>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="text-sm mb-2 block">{label}</label>
      {children}
    </div>
  );
}
