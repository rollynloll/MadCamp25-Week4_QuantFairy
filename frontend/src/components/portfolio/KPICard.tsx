
interface KPIProps {
  label: string;
  value: string;
  subvalue?: string;
  positive?: boolean;
}

export default function KPICard({
  label,
  value,
  subvalue,
  positive,
}: KPIProps) {
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded p-3">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-xl font-semibold font-mono ${positive ? "text-green-500" : ""}`}>
        {value}
      </div>
      {subvalue && (
        <div className={`text-xs font-mono mt-0.5 ${positive ? "text-green-500" : "text-gray-500"}`}>
          {subvalue}
        </div>
      )}
    </div>
  );
}