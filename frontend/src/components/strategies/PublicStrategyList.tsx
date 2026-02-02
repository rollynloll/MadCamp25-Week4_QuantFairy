import { Check } from "lucide-react";
import StrategyCard from "@/components/strategies/StrategyCard";
import type { PublicStrategyListItem } from "@/types/strategy";

interface PublicStrategyListProps {
  strategies: PublicStrategyListItem[];
  addedIds: Set<string>;
  addingIds: Set<string>;
  onSelect: (strategy: PublicStrategyListItem) => void;
  onAdd: (strategy: PublicStrategyListItem) => void;
}

export default function PublicStrategyList({
  strategies,
  addedIds,
  addingIds,
  onSelect,
  onAdd,
}: PublicStrategyListProps) {
  return (
    <div className="space-y-4">
      {strategies.map((strategy) => {
        const isAdded = addedIds.has(strategy.public_strategy_id);
        const isAdding = addingIds.has(strategy.public_strategy_id);
        return (
          <div key={strategy.public_strategy_id} className="relative">
            <div
              className={
                isAdded || isAdding
                  ? "rounded-lg ring-1 ring-green-500/40 bg-green-500/5"
                  : ""
              }
            >
              <StrategyCard
                strategy={strategy}
                onSelect={onSelect}
                onAdd={isAdded || isAdding ? undefined : onAdd}
              />
              {(isAdding || isAdded) && (
                <div className="absolute top-4 right-4 flex items-center gap-1 rounded-full bg-green-600/20 px-2 py-1 text-xs text-green-300">
                  <Check className="w-3 h-3" />
                  {isAdding ? "Adding" : "Added"}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
