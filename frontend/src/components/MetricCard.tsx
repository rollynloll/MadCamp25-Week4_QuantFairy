import { TrendingDown, TrendingUp } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string;
  change: string;
  isPositive: boolean;
  colorValue?: boolean;
  icon: React.ReactNode;
}

export default function MetricCard({
  title,
  value,
  change,
  isPositive,
  colorValue = false,
  icon,
}: MetricCardProps) {
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-gray-400">{title}</span>
        <div className="text-gray-500">{icon}</div>
      </div>
      <div
        className={`text-2xl font-semibold mb-1 ${
          colorValue ? (isPositive ? "text-green-500" : "text-red-500") : ""
        }`}
      >
        {value}
      </div>
      <div className="flex items-center gap-1 text-sm text-gray-400">
        {isPositive && change.startsWith("+") && <TrendingUp className="w-3 h-3" />}
        {!isPositive && change.startsWith("-") && <TrendingDown className="w-3 h-3" />}
        <span>{change}</span>
      </div>
    </div>
  );
}
