import { Download } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

type EquitySeries = {
  key: string;
  name: string;
  stroke: string;
  dashed?: boolean;
};

export default function EquityCurveChart({
  data,
  series,
  height = 300
}: {
  data: Array<Record<string, number | string>>;
  series: EquitySeries[];
  height?: number;
}) {
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold">Equity Curve</h2>
        <button className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <Download className="w-4 h-4" />
          Export Results
        </button>
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="date" stroke="#6b7280" style={{ fontSize: 12 }} />
          <YAxis stroke="#6b7280" style={{ fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "6px",
              fontSize: 12,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {series.map((item) => (
            <Line
              key={item.key}
              type="monotone"
              dataKey={item.key}
              stroke={item.stroke}
              strokeWidth={2}
              name={item.name}
              strokeDasharray={item.dashed ? "5 5" : undefined}
              dot={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
