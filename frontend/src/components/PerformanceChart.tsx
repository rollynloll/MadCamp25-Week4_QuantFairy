import type { Range } from "@/types/dashboard";
import { useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useLanguage } from "@/contexts/LanguageContext";

type Metric = "equity" | "daily_pnl";

type CurvePoint = {
  t: string;
  equity: number;
};
interface Props {
  data: CurvePoint[];
  range: Range;
  onRangeChange: (range: Range) => void;
  loading?: boolean;
}

export default function PerformanceChart({ data, range, onRangeChange, loading }: Props) {
  const ranges: Range[] = ["1D", "1W", "1M", "3M", "1Y", "ALL"];
  
  const rangeLabels: Record<Range, string> = {
    "1D": "1일",
    "1W": "1주",
    "1M": "1개월",
    "3M": "3개월",
    "1Y": "1년",
    "ALL": "전체"
  };

  const formatYAxis = (value: number) => new Intl.NumberFormat("en-US").format(value);

  const [metric, setMetric] = useState<Metric>("equity");
  const metricKey = metric === "equity" ? "equity" : "daily_pnl";
  const { tr } = useLanguage();
  
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold">{tr("Portfolio Performance", "포트폴리오 성과")}</h2>

        <div className="flex items-center gap-3 text-sm">
          <button
            onClick={() => setMetric("equity")}
            className={metric === "equity" ? "text-blue-400" : "text-gray-400 hover:text-white"}
          >
            {tr("Equity", "자산")}
          </button>
          <button
            onClick={() => setMetric("daily_pnl")}
            className={metric === "daily_pnl" ? "text-blue-400" : "text-gray-400 hover:text-white"}
          >
            {tr("Daily P&L", "일별 손익")}
          </button>
        </div>

        <div className="flex items-center gap-4 text-sm">
          {ranges.map((r) => (
            <button
              key={r}
              onClick={() => onRangeChange(r)}
              className={r === range ? "text-blue-400" : "text-gray-400 hover:text-white"}
            >
              {tr(r, rangeLabels[r])}
            </button>
          ))}
        </div>
      </div>

      <div className="relative">
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="t" stroke="#6b7280" style={{ fontSize: 12 }} />
            <YAxis stroke="#6b7280" style={{ fontSize: 12 }} tickFormatter={formatYAxis} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1f2937",
                border: "1px solid #374151",
                borderRadius: "6px",
                fontSize: 12,
              }}
            />
            <Area type="monotone" dataKey={metricKey} stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorValue)" />
          </AreaChart>
        </ResponsiveContainer>
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center text-xs text-gray-400 bg-[#0d1117]/40">
            Updating...
          </div>
        ) : null}
      </div>
    </div>
  );
}
