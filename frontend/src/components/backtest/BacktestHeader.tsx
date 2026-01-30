import { Calendar, Play } from "lucide-react";

export default function BacktestHeader() {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-semibold mb-1">Backtest</h1>
        <p className="text-sm text-gray-400">
          Test strategies against historical data
        </p>
      </div>
      <div className="flex items-center gap-3">
        <button className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm font-medium transition-colors flex items-center gap-2">
          <Calendar className="w-4 h-4" />
          2024-01-01 to 2024-12-31
        </button>
        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition-colors flex items-center gap-2">
          <Play className="w-4 h-4" />
          Run Backtest
        </button>
      </div>
    </div>
  );
}