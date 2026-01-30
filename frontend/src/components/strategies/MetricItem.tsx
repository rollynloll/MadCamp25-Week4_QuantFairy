interface MetricItemProps {
  label: string;
  value: string;
  subValue?: string;
  isPositive: boolean;
}

export default function MetricItem({
  label,
  value,
  subValue,
  isPositive,
}: MetricItemProps) {
  return (
    <div>
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div
        className={`text-sm font-semibold ${
          isPositive ? "text-green-500" : "text-gray-300"
        }`}
      >
        {value}
      </div>
      {subValue && (
        <div
          className={`text-xs ${isPositive ? "text-green-500" : "text-red-500"}`}
        >
          {subValue}
        </div>
      )}
    </div>
  );
}
