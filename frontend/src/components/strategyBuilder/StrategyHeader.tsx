import { useLanguage } from "@/contexts/LanguageContext";
import type { StrategyKpi } from "@/types/strategyBuilder";

interface StrategyHeaderProps {
  name: string;
  description: string;
  onNameChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
  onSave: () => void;
  onRun: () => void;
  liveEnabled: boolean;
  onToggleLive: () => void;
  kpis: StrategyKpi[];
}

export default function StrategyHeader({
  name,
  description,
  onNameChange,
  onDescriptionChange,
  onSave,
  onRun,
  liveEnabled,
  onToggleLive,
  kpis,
}: StrategyHeaderProps) {
  const { tr } = useLanguage();

  return (
    <div className="sticky top-0 z-20 -mx-6 px-6 py-4 bg-[#0b0f17]/95 backdrop-blur border-b border-gray-800">
      <div className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex-1 min-w-[220px]">
            <input
              value={name}
              onChange={(e) => onNameChange(e.target.value)}
              className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm"
              placeholder={tr("Strategy Name", "전략 이름")}
            />
          </div>
          <div className="flex-[2] min-w-[260px]">
            <input
              value={description}
              onChange={(e) => onDescriptionChange(e.target.value)}
              className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm"
              placeholder={tr("Short description", "간단 설명")}
            />
          </div>
          <div className="flex items-center gap-2 ml-auto">
            <button
              type="button"
              onClick={onSave}
              className="px-3 py-2 rounded border border-gray-700 text-sm text-gray-300 hover:text-white hover:border-gray-600"
            >
              {tr("Save", "저장")}
            </button>
            <button
              type="button"
              onClick={onRun}
              className="px-4 py-2 rounded bg-blue-600 text-sm font-medium text-white hover:bg-blue-500"
            >
              {tr("Run Backtest", "백테스트 실행")}
            </button>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">{tr("Live", "라이브")}</span>
            <button
              type="button"
              onClick={onToggleLive}
              className={`relative h-6 w-12 rounded-full border transition-colors ${
                liveEnabled
                  ? "bg-emerald-500/30 border-emerald-500/60"
                  : "bg-gray-800 border-gray-700"
              }`}
            >
              <span
                className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
                  liveEnabled ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
            <span className={`text-xs ${liveEnabled ? "text-emerald-300" : "text-gray-500"}`}>
              {liveEnabled ? tr("On", "켜짐") : tr("Off", "꺼짐")}
            </span>
          </div>

          <div className="flex flex-wrap gap-2 ml-auto">
            {kpis.map((kpi) => (
              <div
                key={kpi.label}
                className="px-3 py-1 rounded-full border border-gray-800 bg-gray-900/40 text-xs text-gray-300"
              >
                <span className="text-gray-500 mr-1">{kpi.label}</span>
                <span className="font-semibold text-white">{kpi.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
