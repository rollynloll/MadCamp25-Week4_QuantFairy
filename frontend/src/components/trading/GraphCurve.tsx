import { useMemo } from "react";
import { TrendingDown, TrendingUp } from "lucide-react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import CustomTooltip from "@/components/trading/CustomTooltip";
import { useLanguage } from "@/contexts/LanguageContext";


const generateChartData = (basePrice: number) => {
  const data = [];
  const now = new Date();
  const marketOpen = new Date(now);
  marketOpen.setHours(9, 30, 0, 0);

  for (let i = 0; i < 390; i += 5) {
    const time = new Date(marketOpen.getTime() + i * 60 * 1000);
    const hours = time.getHours();
    const minutes = time.getMinutes();
    const timeStr = `${hours.toString().padStart(2, "0")}:${minutes.toString().padStart(2, "0")}`;

    const trend = i * 0.002;
    const volatility = Math.sin(i / 20) * 0.5 + Math.random() * 0.3;
    const price = basePrice + trend + volatility;

    data.push({
      time: timeStr,
      price: Number(price.toFixed(2)),
      volume: Math.floor(Math.random() * 50000) + 10000,
    });
  }

  return data;
};

type Props = {
  symbol: string;
  name?: string;
};

const basePriceBySymbol: Record<string, number> = {
  AAPL: 177.5,
  MSFT: 413.0,
  GOOGL: 143.0,
  TSLA: 245.2,
  NVDA: 621.4,
  AMD: 132.75,
};

export default function GraphCurve({ symbol, name }: Props) {
  const { tr } = useLanguage();
  const basePrice = basePriceBySymbol[symbol] ?? 100;
  const chartData = useMemo(() => generateChartData(basePrice), [basePrice, symbol]);
  const currentPrice = chartData[chartData.length - 1].price;
  const openPrice = chartData[0].price;
  const change = currentPrice - openPrice;
  const changePercent = (change / openPrice) * 100;

  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-semibold font-mono">{symbol}</h2>
            <span className="text-sm text-gray-500">
              {name ?? tr("Apple Inc. · NASDAQ", "Apple Inc. · 나스닥")}
            </span>
          </div>
          <div className="flex items-center gap-4 mt-2">
            <span className="text-3xl font-mono font-semibold">
              ${currentPrice.toFixed(2)}
            </span>
            <div
              className={`flex items-center gap-1 text-sm font-mono ${
                change >= 0 ? "text-green-400" : "text-red-400"
              }`}
            >
              {change >= 0 ? (
                <TrendingUp className="w-4 h-4" />
              ) : (
                <TrendingDown className="w-4 h-4" />
              )}
              <span>
                {change >= 0 ? "+" : ""}
                {change.toFixed(2)} ({changePercent.toFixed(2)}%)
              </span>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded text-xs font-medium transition-colors">
            1D
          </button>
          <button className="px-3 py-1.5 bg-blue-600/20 text-blue-400 rounded text-xs font-medium">
            5D
          </button>
          <button className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded text-xs font-medium transition-colors">
            1M
          </button>
          <button className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded text-xs font-medium transition-colors">
            3M
          </button>
          <button className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded text-xs font-medium transition-colors">
            1Y
          </button>
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
                  stopColor={change >= 0 ? "#10b981" : "#ef4444"}
                  stopOpacity={0.3}
                />
                <stop
                  offset="95%"
                  stopColor={change >= 0 ? "#10b981" : "#ef4444"}
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis
              dataKey="time"
              stroke="#6b7280"
              tick={{ fill: "#9ca3af", fontSize: 11 }}
              tickLine={{ stroke: "#374151" }}
              interval={20}
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
              stroke={change >= 0 ? "#10b981" : "#ef4444"}
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
              ${openPrice.toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-1">{tr("High", "고가")}</div>
            <div className="text-sm font-mono font-semibold text-green-400">
              ${Math.max(...chartData.map((d) => d.price)).toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-1">{tr("Low", "저가")}</div>
            <div className="text-sm font-mono font-semibold text-red-400">
              ${Math.min(...chartData.map((d) => d.price)).toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-1">{tr("Volume", "거래량")}</div>
            <div className="text-sm font-mono font-semibold">
              {(
                chartData.reduce((sum, d) => sum + d.volume, 0) / 1000000
              ).toFixed(2)}
              M
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-1">{tr("Avg Vol", "평균 거래량")}</div>
            <div className="text-sm font-mono font-semibold">
              {(
                chartData.reduce((sum, d) => sum + d.volume, 0) /
              chartData.length /
              1000
            ).toFixed(0)}
            K
          </div>
        </div>
      </div>
    </div>
  );
}