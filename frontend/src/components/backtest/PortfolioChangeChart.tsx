import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList } from "recharts";

export type PortfolioChangePoint = {
  month: string;
  cash: number;
  top_symbol?: string;
  [key: string]: number | string | undefined;
};

export type PortfolioHoldingsSeries = {
  key: string;
  name: string;
  color: string;
};

export default function PortfolioChangeChart({
  data,
  series
}: {
  data: PortfolioChangePoint[];
  series: PortfolioHoldingsSeries[];
}) {
  const renderLabel = (props: any) => {
    const { x, y, width, payload } = props;
    const symbol = payload?.top_symbol;
    if (!symbol) return null;
    const posX = x + width / 2;
    const posY = y - 6;
    return (
      <text x={posX} y={posY} fill="#9ca3af" fontSize={10} textAnchor="middle">
        {symbol}
      </text>
    );
  };

  const renderTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    const items = payload
      .map((item: any) => ({
        name: item.name as string,
        value: Number(item.value) || 0
      }))
      .filter((item) => item.value > 0)
      .sort((a, b) => b.value - a.value);
    return (
      <div className="bg-[#1f2937] border border-gray-700 rounded px-3 py-2 text-xs text-gray-100">
        <div className="text-gray-400 mb-1">{label}</div>
        <div className="max-h-40 overflow-y-auto space-y-0.5">
          {items.map((item) => (
            <div key={item.name}>{`${item.name}: ${item.value.toFixed(2)}%`}</div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-6">Portfolio Holdings (All)</h2>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="month" stroke="#6b7280" style={{ fontSize: 12 }} />
          <YAxis
            stroke="#6b7280"
            style={{ fontSize: 12 }}
            tickFormatter={(value) => `${value}%`}
          />
          <Tooltip content={renderTooltip} />
          {series.map((item) => (
            <Bar
              key={item.key}
              dataKey={item.key}
              stackId="1"
              fill={item.color}
              fillOpacity={0.85}
              name={item.name}
            >
              {item.key === "cash" ? (
                <LabelList dataKey="top_symbol" content={renderLabel} />
              ) : null}
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
