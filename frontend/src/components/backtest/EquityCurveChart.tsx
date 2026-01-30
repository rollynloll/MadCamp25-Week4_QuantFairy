import { Download } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import type { EquityPoint } from "@/types/backtest";

export default function EquityCurveChart({ data }: { data: EquityPoint[] }) {
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold">Equity Curve</h2>
        <button className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <Download className="w-4 h-4" />
          Export Results
        </button>
      </div>
      <ResponsiveContainer width="100%" height={300}>
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
          <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} name="Strategy" dot={false} />
          <Line type="monotone" dataKey="benchmark" stroke="#6b7280" strokeWidth={2} name="Benchmark" strokeDasharray="5 5" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}