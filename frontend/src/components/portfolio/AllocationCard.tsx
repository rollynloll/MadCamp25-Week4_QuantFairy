import type { AllocationItem } from "@/types/portfolio";

export default function AllocationCard({ allocation }: { allocation: AllocationItem[]; }) {
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">Allocation</h2>
      <div className="space-y-4">
        {allocation.map((item) => (
          <div key={item.category}>
            <div className="flex items-center justify-between mb-2 text-sm">
              <span className="text-gray-300">{item.category}</span>
              <span className="font-semibold">{item.value}%</span>
            </div>
            <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-600"
                style={{ width: `${item.value}%` }}
              />
            </div>
            <div className="text-xs text-gray-500 mt-1">
              ${item.amount.toLocaleString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}