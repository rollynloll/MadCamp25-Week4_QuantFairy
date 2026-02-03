import { AlertCircle, ChevronDown, ChevronUp } from "lucide-react";
import MetricItem from "./MetricItem";
import type { SectorAllocationItem, Strategy } from "@/types/portfolio";
import StateToggle from "./StateToggle";
import { useLanguage } from "@/contexts/LanguageContext";

type tab = "strategy" | "sector" | "exposure";
interface AllocationProps {
  tab: tab;
  onTabChange: (tab: tab) => void;
  strategies: Strategy[];
  sectorAllocation: SectorAllocationItem[];
  targetWeights: Record<string, number>;
  onTargetWeightChange: (id: string, value: number) => void;
  derivedCash: number;
  totalTarget: number;

  hasUnsavedChanges: boolean;
  onReset: () => void;
  onSave: () => void;
  
  showAdvanced: boolean;
  onToggleAdvanced: () => void;
  saveError?: string | null;
  isSaving?: boolean;
  saveStatus?: string | null;
}

export default function AllocationCard({
  tab,
  onTabChange,
  strategies,
  sectorAllocation,
  targetWeights,
  onTargetWeightChange,
  derivedCash,
  totalTarget,
  hasUnsavedChanges,
  onReset,
  onSave,
  showAdvanced,
  onToggleAdvanced,
  saveError,
  isSaving,
  saveStatus
}: AllocationProps) {
  const { tr } = useLanguage();

  const overAllocatedBy = Math.max(0, totalTarget - 100);
  const canSave = hasUnsavedChanges && overAllocatedBy <= 0 && !isSaving;
  const trackStyle = (value: number, max: number) => ({
    background: `linear-gradient(to right, #2563eb 0%, #2563eb ${
      (value / max) * 100
    }%, #1f2937 ${(value / max) * 100}%, #1f2937 100%)`,
  });

  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded flex flex-col h-fit max-h-[600px]">
      {/* Tabs */}
      <div className="flex border-b border-gray-800">
        <button
          onClick={() => onTabChange("strategy")}
          className={`flex-1 py-3 text-sm font-medium transition-colors ${
            tab === "strategy" ? "text-white border-b-2 border-blue-500" : "text-gray-500"
          }`}
        >
          {tr("Strategy", "전략")}
        </button>
        <button
          onClick={() => onTabChange("sector")}
          className={`flex-1 py-3 text-sm font-medium transition-colors ${
            tab === "sector" ? "text-white border-b-2 border-blue-500" : "text-gray-500"
          }`}
        >
          {tr("Sector", "섹터")}
        </button>
        <button
          onClick={() => onTabChange("exposure")}
          className={`flex-1 py-3 text-sm font-medium transition-colors ${
            tab === "exposure" ? "text-white border-b-2 border-blue-500" : "text-gray-500"
          }`}
        >
          {tr("Exposure", "노출 비중")}
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-auto">
        {tab === "strategy" && (
          <div className="p-4 space-y-4">
            {/* Portfolio Constraints */}
            <div className="p-3 bg-gray-900/30 rounded border border-gray-800">
              <div className="text-xs font-semibold text-gray-400 mb-3">
                {tr("Portfolio Constraints", "포트폴리오 제약 조건")}
              </div>
              <div className="space-y-3">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-xs text-gray-400">{tr("Cash (auto)", "현금 (자동)")}</label>
                    <div className="text-xs font-mono text-gray-200">
                      {derivedCash.toFixed(1)}%
                    </div>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="0.5"
                    value={derivedCash}
                    disabled
                    style={trackStyle(derivedCash, 100)}
                    className="w-full h-1.5 rounded appearance-none cursor-not-allowed accent-blue-600 disabled:opacity-100"
                  />
                  <div className="text-[11px] text-gray-500">
                    {tr("Total strategy allocation", "전략 합계")}: {totalTarget.toFixed(1)}%
                  </div>
                </div>

                {/* Advanced Constraints */}
                <button
                  onClick={onToggleAdvanced}
                  className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 transition-colors"
                >
                  {showAdvanced ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  {tr("Advanced", "고급 설정")}
                </button>
                {showAdvanced && (
                  <div className="pl-4 space-y-2 text-xs text-gray-500">
                    <div>{tr("Max strategy weight: 35%", "전략 최대 비중: 35%")}</div>
                    <div>{tr("Min strategy weight: 5%", "전략 최소 비중: 5%")}</div>
                    <div>{tr("Rebalance tolerance: 2%", "리밸런스 허용 오차: 2%")}</div>
                  </div>
                )}
              </div>
            </div>

            {/* Strategy List */}
            <div className="space-y-2">
              {strategies.map((strategy) => {
                const isPaused = strategy.state === "paused";
                const targetValue = isPaused
                  ? strategy.currentWeight
                  : (targetWeights[strategy.id] ?? strategy.currentWeight);
                return (
                <div
                  key={strategy.id}
                  className={`p-3 bg-gray-900/20 rounded border border-gray-800 ${
                    isPaused ? "opacity-70" : ""
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-medium text-sm">{strategy.name}</div>
                    <StateToggle state={strategy.state} />
                  </div>

                  <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
                    <span>{tr("Current", "현재")}: {strategy.currentWeight.toFixed(1)}%</span>
                    <span>{tr("Target", "목표")}: {targetValue.toFixed(1)}%</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min="0"
                      max="40"
                      step="0.5"
                      value={targetValue}
                      disabled={isPaused}
                      onChange={(e) => onTargetWeightChange(strategy.id, Number(e.target.value))}
                      style={trackStyle(targetValue, 40)}
                      className="flex-1 h-1.5 rounded appearance-none cursor-pointer accent-blue-600 disabled:cursor-not-allowed"
                    />

                    <input
                      type="number"
                      value={targetValue}
                      disabled={isPaused}
                      onChange={(e) => onTargetWeightChange(strategy.id, Number(e.target.value))}
                      className="w-14 bg-[#0a0d14] border border-gray-800 rounded px-2 py-1 text-xs text-right font-mono disabled:cursor-not-allowed"
                      step="0.5"
                    />
                  </div>
                </div>
              )})}
            </div>

            <div className="text-xs text-gray-500 pt-2">
              {tr("Changes will be applied at the next scheduled rebalance", "변경 사항은 다음 리밸런싱 시 적용됩니다")}
            </div>
          </div>
        )}

        {tab === "sector" && (
          <div className="p-4 space-y-3">
            {sectorAllocation.map((sector) => (
              <div key={sector.sector}>
                <div className="flex items-center justify-between mb-1.5 text-sm">
                  <span>{sector.sector}</span>
                  <span className="font-mono text-xs text-gray-400">
                    {sector.percent.toFixed(1)}% · ${sector.value.toLocaleString()}
                  </span>
                </div>
                <div className="h-6 bg-gray-900 rounded overflow-hidden">
                  <div
                    className="h-full bg-blue-600/40"
                    style={{ width: `${sector.percent}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "exposure" && (
          <div className="p-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <MetricItem label={tr("Net Exposure", "순 노출도")} value="87.5%" />
              <MetricItem label={tr("Gross Exposure", "총 노출도")} value="97.7%" />
              <MetricItem label={tr("Cash", "현금")} value="12.5%" />
              <MetricItem label={tr("Top 5 Concentration", "상위 5종목 집중도")} value="76.8%" />
            </div>
          </div>
        )}
      </div>

      {/* Sticky Action Bar */}
      {tab === "strategy" && (
        <div className="border-t border-gray-800 p-3 bg-[#0d1117]">
          {hasUnsavedChanges && (
            <div className="flex items-center gap-2 text-xs text-yellow-500 mb-2">
              <AlertCircle className="w-3 h-3" />
              {tr("Unsaved changes", "저장되지 않은 변경사항")}
            </div>
          )}
          {overAllocatedBy > 0 && (
            <div className="flex items-center gap-2 text-xs text-red-400 mb-2">
              <AlertCircle className="w-3 h-3" />
              {tr("Over-allocated by", "초과 비중")}: {overAllocatedBy.toFixed(1)}%
            </div>
          )}
          {saveError && (
            <div className="flex items-center gap-2 text-xs text-red-400 mb-2">
              <AlertCircle className="w-3 h-3" />
              {saveError}
            </div>
          )}
          {saveStatus && !saveError && (
            <div className="flex items-center gap-2 text-xs text-green-400 mb-2">
              <AlertCircle className="w-3 h-3" />
              {saveStatus}
            </div>
          )}
          <div className="flex gap-2">
            <button
              onClick={onReset}
              className="flex-1 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm font-medium transition-colors"
              disabled={!hasUnsavedChanges || isSaving}
            >
              {tr("Reset", "초기화")}
            </button>
            <button
              onClick={onSave}
              className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition-colors disabled:opacity-50"
              disabled={!canSave}
            >
              {isSaving ? tr("Saving...", "저장 중...") : tr("Save Targets", "목표 저장")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
