import { AlertCircle, ChevronDown, ChevronUp } from "lucide-react";
import MetricItem from "./MetricItem";
import type { SectorAllocationItem, Strategy } from "@/types/portfolio";
import StateToggle from "./StateToggle";

type tab = "strategy" | "sector" | "exposure";
interface AllocationProps {
  tab: tab;
  onTabChange: (tab: tab) => void;
  strategies: Strategy[];
  sectorAllocation: SectorAllocationItem[];
  targetWeights: Record<number, number>;
  onTargetWeightChange: (id: number, value: number) => void;
  targetCash: number;
  onTargetCashChange: (value: number) => void;

  hasUnsavedChanges: boolean;
  onReset: () => void;
  onSave: () => void;
  
  showAdvanced: boolean;
  onToggleAdvanced: () => void;
}

export default function AllocationCard({ 
  tab,
  onTabChange,
  strategies,
  sectorAllocation,
  targetWeights,
  onTargetWeightChange,
  targetCash,
  onTargetCashChange,
  hasUnsavedChanges,
  onReset,
  onSave,
  showAdvanced,
  onToggleAdvanced
}: AllocationProps) {
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
          Strategy
        </button>
        <button
          onClick={() => onTabChange("sector")}
          className={`flex-1 py-3 text-sm font-medium transition-colors ${
            tab === "sector" ? "text-white border-b-2 border-blue-500" : "text-gray-500"
          }`}
        >
          Sector
        </button>
        <button
          onClick={() => onTabChange("exposure")}
          className={`flex-1 py-3 text-sm font-medium transition-colors ${
            tab === "exposure" ? "text-white border-b-2 border-blue-500" : "text-gray-500"
          }`}
        >
          Exposure
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-auto">
        {tab === "strategy" && (
          <div className="p-4 space-y-4">
            {/* Portfolio Constraints */}
            <div className="p-3 bg-gray-900/30 rounded border border-gray-800">
              <div className="text-xs font-semibold text-gray-400 mb-3">Portfolio Constraints</div>
              <div className="space-y-3">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-xs text-gray-400">Target Cash %</label>
                    <input
                      type="number"
                      value={targetCash}
                      onChange={(e) => {
                        onTargetCashChange(Number(e.target.value));
                      }}
                      className="w-16 bg-[#0a0d14] border border-gray-800 rounded px-2 py-1 text-xs text-right font-mono"
                      step="0.5"
                    />
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="50"
                    step="0.5"
                    value={targetCash}
                    onChange={(e) => {
                      onTargetCashChange(Number(e.target.value));
                    }}
                    className="w-full h-1.5 bg-gray-800 rounded appearance-none cursor-pointer accent-blue-600"
                  />
                </div>

                {/* Advanced Constraints */}
                <button
                  onClick={onToggleAdvanced}
                  className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 transition-colors"
                >
                  {showAdvanced ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  Advanced
                </button>
                {showAdvanced && (
                  <div className="pl-4 space-y-2 text-xs text-gray-500">
                    <div>Max strategy weight: 35%</div>
                    <div>Min strategy weight: 5%</div>
                    <div>Rebalance tolerance: 2%</div>
                  </div>
                )}
              </div>
            </div>

            {/* Strategy List */}
            <div className="space-y-2">
              {strategies.map((strategy) => (
                <div key={strategy.id} className="p-3 bg-gray-900/20 rounded border border-gray-800">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-medium text-sm">{strategy.name}</div>
                    <StateToggle state={strategy.state} />
                  </div>

                  <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
                    <span>Current: {strategy.currentWeight.toFixed(1)}%</span>
                    <span>Target: {targetWeights[strategy.id]?.toFixed(1) ?? "—"}%</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min="0"
                      max="40"
                      step="0.5"
                      value={targetWeights[strategy.id] ?? 0}
                      onChange={(e) => onTargetWeightChange(strategy.id, Number(e.target.value))}
                      className="flex-1 h-1.5 bg-gray-800 rounded appearance-none cursor-pointer accent-blue-600"
                    />

                    <input
                      type="number"
                      value={targetWeights[strategy.id] ?? 0}
                      onChange={(e) => onTargetWeightChange(strategy.id, Number(e.target.value))}
                      className="w-14 bg-[#0a0d14] border border-gray-800 rounded px-2 py-1 text-xs text-right font-mono"
                      step="0.5"
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="text-xs text-gray-500 pt-2">
              Changes will be applied at the next scheduled rebalance
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
              <MetricItem label="Net Exposure" value="87.5%" />
              <MetricItem label="Gross Exposure" value="97.7%" />
              <MetricItem label="Cash" value="12.5%" />
              <MetricItem label="Top 5 Concentration" value="76.8%" />
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
              Unsaved changes
            </div>
          )}
          <div className="flex gap-2">
            <button
              onClick={onReset}
              className="flex-1 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm font-medium transition-colors"
              disabled={!hasUnsavedChanges}
            >
              Reset
            </button>
            <button
              onClick={onSave}
              className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition-colors disabled:opacity-50"
              disabled={!hasUnsavedChanges}
            >
              Save Targets
            </button>
          </div>
        </div>
      )}
    </div>
  );
}