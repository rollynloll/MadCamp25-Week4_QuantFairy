interface MetricProps { 
  label: string; 
  value: string 
}

export default function MetricItem({ label, value }: MetricProps) {
  return (
    <div>
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className="font-semibold font-mono">{value}</div>
    </div>
  );
}