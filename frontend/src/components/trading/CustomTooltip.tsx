export default function CustomTooltip ({ active, payload }: any) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#0d1117] border border-gray-700 rounded px-3 py-2">
        <p className="text-xs text-gray-400 mb-1">{payload[0].payload.time}</p>
        <p className="text-sm font-mono font-semibold">
          ${payload[0].value.toFixed(2)}
        </p>
        <p className="text-xs text-gray-500 mt-1">
          Vol: {payload[0].payload.volume.toLocaleString()}
        </p>
      </div>
    );
  }
  return null;
};