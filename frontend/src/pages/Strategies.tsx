import StrategyCard from "@/components/strategies/StrategyCard";
import { useStrategies } from "@/hooks/useStrategies";

export default function Strategies() {
  const { data, loading, error } = useStrategies();

  if (loading) {
    return <div className="text-sm text-gray-400">Loading strategies...</div>;
  }

  if (error || !data) {
    return (
      <div className="text-sm text-red-400">
        {error ?? "Failed to load strategies"}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold mb-1">Strategies</h1>
          <p className="text-sm text-gray-400">
            Manage and monitor your trading strategies
          </p>
        </div>
        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition-colors">
          + New Strategy
        </button>
      </div>

      <div className="space-y-4">
        {data.map((strategy) => (
          <StrategyCard key={strategy.id} strategy={strategy} />
        ))}
      </div>
    </div>
  );
}
