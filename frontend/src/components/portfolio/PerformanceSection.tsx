import type { DrawdownPoint, EquityPoint } from "@/types/portfolio";
import { Area, AreaChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useLanguage } from "@/contexts/LanguageContext";

interface PerformanceProps {
  equityCurve: EquityPoint[];
  drawdownData: DrawdownPoint[];
  timeRange: string;
  onTimeRangeChange: (range: string) => void;
  showBenchmark: boolean;
  onShowBenchmarkChange: (next: boolean) => void;
}

export default function PerformanceSection({
  equityCurve,
  drawdownData,
  timeRange,
  onTimeRangeChange,
  showBenchmark,
  onShowBenchmarkChange
}: PerformanceProps ) {
  const { tr } = useLanguage();

  const rangeLabels: Record<string, string> = {
    "1W": "1주",
    "1M": "1개월",
    "3M": "3개월",
    "1Y": "1년",
    "ALL": "전체"
  };

  return (
    <div>
      <h2 className="font-semibold mb-4">{tr("Performance", "성과")}</h2>
      <div className="grid grid-cols-2 gap-6">
        {/* Equity Curve */}
        <div className="bg-[#0d1117] border border-gray-800 rounded p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium">{tr("Equity Curve", "자산 곡선")}</h3>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1">
                {["1W", "1M", "3M", "1Y", "ALL"].map((range) => (
                  <button
                    key={range}
                    onClick={() => onTimeRangeChange(range)}
                    className={`px-2 py-1 text-xs rounded transition-colors ${
                      timeRange === range ? "bg-blue-600 text-white" : "text-gray-500 hover:text-gray-300"
                    }`}
                  >
                    {tr(range, rangeLabels[range])}
                  </button>
                ))}
              </div>
              <label className="flex items-center gap-1.5 text-xs text-gray-500 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showBenchmark}
                  onChange={(e) => onShowBenchmarkChange(e.target.checked)}
                  className="w-3 h-3"
                />
                SPY
              </label>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={equityCurve}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
              <XAxis dataKey="date" stroke="#6b7280" style={{ fontSize: 11 }} />
              <YAxis stroke="#6b7280" style={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1f2937",
                  border: "1px solid #374151",
                  borderRadius: "4px",
                  fontSize: 12,
                }}
              />
              <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Drawdown + Metrics */}
        <div className="space-y-4">
          <div className="bg-[#0d1117] border border-gray-800 rounded p-4">
            <h3 className="text-sm font-medium mb-4">{tr("Drawdown", "낙폭")}</h3>
            <ResponsiveContainer width="100%" height={140}>
              <AreaChart data={drawdownData}>
                <defs>
                  <linearGradient id="drawdownGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis dataKey="date" stroke="#6b7280" style={{ fontSize: 11 }} />
                <YAxis stroke="#6b7280" style={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #374151",
                    borderRadius: "4px",
                    fontSize: 12,
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#ef4444"
                  strokeWidth={2}
                  fill="url(#drawdownGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-[#0d1117] border border-gray-800 rounded p-4">
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <div className="text-xs text-gray-500 mb-1">{tr("CAGR", "연평균 수익률")}</div>
                <div className="font-semibold text-green-500">+28.9%</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">{tr("Sharpe", "샤프 지수")}</div>
                <div className="font-semibold">2.34</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">{tr("Max DD", "최대 낙폭")}</div>
                <div className="font-semibold text-red-500">-5.2%</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
