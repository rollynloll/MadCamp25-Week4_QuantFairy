import { Calendar, Play } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface BacktestHeaderProps {
  rangeLabel?: string;
  startDate?: string;
  endDate?: string;
  onStartDateChange?: (value: string) => void;
  onEndDateChange?: (value: string) => void;
  rangeDisabled?: boolean;
  onRun?: () => void;
  runDisabled?: boolean;
}

export default function BacktestHeader({
  rangeLabel = "2024-01-01 to 2024-12-31",
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  rangeDisabled = false,
  onRun,
  runDisabled = false
}: BacktestHeaderProps) {
  const { tr } = useLanguage();
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-semibold mb-1">{tr("Backtest", "백테스트")}</h1>
        <p className="text-sm text-gray-400">
          {tr("Test strategies against historical data", "과거 데이터를 기준으로 전략을 테스트합니다")}
        </p>
      </div>
      <div className="flex items-center gap-5">
        <div className="px-3 py-2 bg-gray-800 rounded text-sm font-medium flex items-center gap-3">
          <input
            type="date"
            value={startDate ?? ""}
            onChange={(event) => onStartDateChange?.(event.target.value)}
            disabled={rangeDisabled}
            className="bg-transparent text-gray-200 text-sm focus:outline-none"
          />
          <span className="text-gray-400 text-xs">{tr("to", "부터")}</span>
          <input
            type="date"
            value={endDate ?? ""}
            onChange={(event) => onEndDateChange?.(event.target.value)}
            disabled={rangeDisabled}
            className="bg-transparent text-gray-200 text-sm focus:outline-none"
          />
          {!startDate && !endDate && (
            <span className="text-gray-300">{rangeLabel}</span>
          )}
        </div>
        <button
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-900 disabled:text-gray-300 disabled:cursor-not-allowed rounded text-sm font-medium transition-colors flex items-center gap-2"
          onClick={onRun}
          disabled={runDisabled}
        >
          <Play className="w-4 h-4" />
          {tr("Run Backtest", "백테스트 실행")}
        </button>
      </div>
    </div>
  );
}
