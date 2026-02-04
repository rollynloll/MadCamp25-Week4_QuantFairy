import { useMemo } from "react";
import { TrendingDown, TrendingUp } from "lucide-react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import CustomTooltip from "@/components/trading/CustomTooltip";
import { useLanguage } from "@/contexts/LanguageContext";
import type { BarPoint } from "@/hooks/useMarketStream";

type Props = {
  symbol: string;
  name?: string;
  bars: BarPoint[];
  timeframe: "1D" | "1W" | "1M" | "3M" | "1Y";
  onTimeframeChange?: (value: "1D" | "1W" | "1M" | "3M" | "1Y") => void;
};

const formatTime = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const hours = date.getHours().toString().padStart(2, "0");
  const minutes = date.getMinutes().toString().padStart(2, "0");
  return `${hours}:${minutes}`;
};

const formatTick = (value: string, timeframe: Props["timeframe"]) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  if (timeframe === "1D") {
    const hours = date.getHours().toString().padStart(2, "0");
    const minutes = date.getMinutes().toString().padStart(2, "0");
    return `${hours}:${minutes}`;
  }
  if (timeframe === "1W" || timeframe === "1M" || timeframe === "3M") {
    return `${date.getMonth() + 1}/${date.getDate()}`;
  }
  return `${date.getMonth() + 1}/${String(date.getFullYear()).slice(-2)}`;
};

const estimatePointsPerDay = (bars: BarPoint[]) => {
  if (bars.length < 2) return 1;
  const diffs: number[] = [];
  const samples = Math.min(bars.length - 1, 50);
  for (let i = 1; i <= samples; i += 1) {
    const prev = new Date(bars[i - 1].time).getTime();
    const next = new Date(bars[i].time).getTime();
    if (Number.isNaN(prev) || Number.isNaN(next)) continue;
    const diffMinutes = Math.abs(next - prev) / 60000;
    if (diffMinutes > 0) diffs.push(diffMinutes);
  }
  if (!diffs.length) return 1;
  diffs.sort((a, b) => a - b);
  const median = diffs[Math.floor(diffs.length / 2)];
  return Math.max(1, Math.round(1440 / median));
};

export default function GraphCurve({ symbol, name, bars, timeframe, onTimeframeChange }: Props) {
  const { tr } = useLanguage();
  const pointsPerDay = useMemo(() => estimatePointsPerDay(bars), [bars]);
  const tickInterval = useMemo(() => {
    if (timeframe === "1D") return 20;
    if (timeframe === "1Y") return 20;
    return Math.max(pointsPerDay - 1, 0);
  }, [timeframe, pointsPerDay]);
  const chartData = useMemo(
    () =>
      bars.map((bar) => ({
        time: formatTime(bar.time),
        rawTime: bar.time,
        price: Number(bar.close.toFixed(2)),
        volume: bar.volume,
      })),
    [bars]
  );

  const stats = useMemo(() => {
    if (!bars.length) {
      return {
        hasData: false,
        currentPrice: 0,
        openPrice: 0,
        change: 0,
        changePercent: 0,
        high: 0,
        low: 0,
        volumeTotal: 0,
        avgVolume: 0,
      };
    }
    const currentPrice = bars[bars.length - 1].close;
    const openPrice = bars[0].open;
    const change = currentPrice - openPrice;
    const changePercent = openPrice ? (change / openPrice) * 100 : 0;
    const high = Math.max(...bars.map((bar) => bar.high));
    const low = Math.min(...bars.map((bar) => bar.low));
    const volumeTotal = bars.reduce((sum, bar) => sum + bar.volume, 0);
    const avgVolume = volumeTotal / bars.length;
    return {
      hasData: true,
      currentPrice,
      openPrice,
      change,
      changePercent,
      high,
      low,
      volumeTotal,
      avgVolume,
    };
  }, [bars]);

  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-semibold font-mono">{symbol}</h2>
            <span className="text-sm text-gray-500">
              {name ?? "Apple Inc. NASDAQ"}
            </span>
          </div>
          <div className="flex items-center gap-4 mt-2">
            <span className="text-3xl font-mono font-semibold">
              {stats.hasData ? `$${stats.currentPrice.toFixed(2)}` : "--"}
            </span>
            <div
              className={`flex items-center gap-1 text-sm font-mono ${
                stats.change >= 0 ? "text-green-400" : "text-red-400"
              }`}
            >
              {stats.change >= 0 ? (
                <TrendingUp className="w-4 h-4" />
              ) : (
                <TrendingDown className="w-4 h-4" />
              )}
              <span>
                {stats.change >= 0 ? "+" : ""}
                {stats.hasData ? stats.change.toFixed(2) : "--"} (
                {stats.hasData ? stats.changePercent.toFixed(2) : "--"}%)
              </span>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          {(["1D", "1W", "1M", "3M", "1Y"] as const).map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => onTimeframeChange?.(value)}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                timeframe === value
                  ? "bg-blue-600/20 text-blue-400"
                  : "bg-gray-800 hover:bg-gray-700 text-gray-300"
              }`}
            >
              {value}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="h-[500px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor={stats.change >= 0 ? "#10b981" : "#ef4444"}
                  stopOpacity={0.3}
                />
                <stop
                  offset="95%"
                  stopColor={stats.change >= 0 ? "#10b981" : "#ef4444"}
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis
              dataKey="rawTime"
              stroke="#6b7280"
              tick={{ fill: "#9ca3af", fontSize: 11 }}
              tickLine={{ stroke: "#374151" }}
              interval={tickInterval}
              tickFormatter={(value) => formatTick(value, timeframe)}
            />
            <YAxis
              stroke="#6b7280"
              tick={{ fill: "#9ca3af", fontSize: 11 }}
              tickLine={{ stroke: "#374151" }}
              domain={["dataMin - 0.5", "dataMax + 0.5"]}
              tickFormatter={(value) => `$${value.toFixed(2)}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="price"
              stroke={stats.change >= 0 ? "#10b981" : "#ef4444"}
              strokeWidth={2}
              fill="url(#colorPrice)"
              animationDuration={300}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-5 gap-4 mt-6 pt-6 border-t border-gray-800">
        <div>
          <div className="text-xs text-gray-500 mb-1">{tr("Open", "시가")}</div>
          <div className="text-sm font-mono font-semibold">
            {stats.hasData ? `$${stats.openPrice.toFixed(2)}` : "--"}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">{tr("High", "고가")}</div>
          <div className="text-sm font-mono font-semibold text-green-400">
            {stats.hasData ? `$${stats.high.toFixed(2)}` : "--"}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">{tr("Low", "저가")}</div>
          <div className="text-sm font-mono font-semibold text-red-400">
            {stats.hasData ? `$${stats.low.toFixed(2)}` : "--"}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">{tr("Volume", "거래량")}</div>
          <div className="text-sm font-mono font-semibold">
            {stats.hasData ? (stats.volumeTotal / 1000000).toFixed(2) : "--"}
            {stats.hasData ? " M" : ""}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">{tr("Avg Vol", "평균 거래량")}</div>
          <div className="text-sm font-mono font-semibold">
            {stats.hasData ? (stats.avgVolume / 1000).toFixed(0) : "--"}
            {stats.hasData ? " K" : ""}
          </div>
        </div>
      </div>
    </div>
  );
}
