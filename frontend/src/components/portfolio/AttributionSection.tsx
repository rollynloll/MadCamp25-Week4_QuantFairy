import type { PortfolioAttributionResponse } from "@/types/portfolio";
import { useLanguage } from "@/contexts/LanguageContext";

interface AttributionSectionProps {
  attribution: PortfolioAttributionResponse;
}

export default function AttributionSection({ attribution }: AttributionSectionProps) {
  const { tr } = useLanguage();
  const rows = attribution.items.map((item) => ({
    key: item.key,
    label: item.label,
    exposurePct: item.exposure_pct,
    pnl: item.unrealized_pnl_value,
    contribution: item.period_contribution_pct
  }));

  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">{tr("Attribution", "기여도")}</h2>
        <span className="text-xs text-gray-500">
          {attribution.by === "sector" ? tr("By Sector", "색터 기준") : tr("By Strategy", "전략 기준")}
        </span>
      </div>
      {rows.length === 0 ? (
        <div className="text-sm text-gray-400">{tr("No attribution data.", "기여도 데이터가 없습니다.")}</div>
      ) : (
        <div className="space-y-2">
          {rows.map((row) => (
            <div
              key={row.key}
              className="flex items-center justify-between rounded border border-gray-800 bg-[#0a0d14] px-4 py-3 text-sm"
            >
              <div className="font-medium">{row.label}</div>
              <div className="flex items-center gap-6 text-xs text-gray-400">
                <span className="font-mono">{row.exposurePct.toFixed(1)}%</span>
                <span className="font-mono">
                  {row.pnl >= 0 ? "+" : "-"}${Math.abs(row.pnl).toFixed(2)}
                </span>
                <span className="font-mono">
                  {row.contribution !== undefined
                    ? `${row.contribution >= 0 ? "+" : ""}${row.contribution.toFixed(2)}%`
                    : "-"}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
