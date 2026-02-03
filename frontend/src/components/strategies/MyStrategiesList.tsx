import { Minus } from "lucide-react";
import StrategyCard from "@/components/strategies/StrategyCard";
import type { MyStrategy, PublicStrategyListItem } from "@/types/strategy";
import { useLanguage } from "@/contexts/LanguageContext";

interface MyStrategiesListProps {
  fromPublic: PublicStrategyListItem[];
  custom: MyStrategy[];
  onSelect: (strategy: PublicStrategyListItem) => void;
  onRemovePublic: (strategy: PublicStrategyListItem) => void;
  onRemoveCustom: (myStrategyId: string) => void;
}

export default function MyStrategiesList({
  fromPublic,
  custom,
  onSelect,
  onRemovePublic,
  onRemoveCustom,
}: MyStrategiesListProps) {
  const { tr } = useLanguage();
  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <div className="text-xs uppercase tracking-wide text-gray-500">
          {tr("From Public Strategies", "공개 전략에서 추가")}
        </div>
        {fromPublic.length === 0 ? (
          <div className="text-sm text-gray-400">
            {tr("No strategies added from Public.", "공개 전략에서 추가된 항목이 없습니다.")}
          </div>
        ) : (
          <div className="space-y-4">
            {fromPublic.map((strategy) => (
              <StrategyCard
                key={strategy.public_strategy_id}
                strategy={strategy}
                onSelect={onSelect}
                onRemove={onRemovePublic}
              />
            ))}
          </div>
        )}
      </div>

      <div className="space-y-3">
        <div className="text-xs uppercase tracking-wide text-gray-500">
          {tr("Custom Strategies", "커스텀 전략")}
        </div>
        {custom.length === 0 ? (
          <div className="text-sm text-gray-400">{tr("No custom strategies yet.", "커스텀 전략이 없습니다.")}</div>
        ) : (
          <div className="space-y-4">
            {custom.map((strategy) => (
              <div
                key={strategy.my_strategy_id}
                className="bg-[#0d1117] border border-gray-800 rounded-lg p-6"
              >
                <div className="flex items-start justify-between gap-6 mb-3">
                  <div>
                    <h3 className="text-lg font-semibold">{strategy.name}</h3>
                    {strategy.note && (
                      <p className="text-sm text-gray-400 mt-1">
                        {strategy.note}
                      </p>
                    )}
                  </div>
                  <button
                    onClick={() => onRemoveCustom(strategy.my_strategy_id)}
                    className="p-2.5 hover:bg-gray-800 rounded transition-colors"
                    title="Remove"
                    type="button"
                  >
                    <Minus size={18} />
                  </button>
                </div>
                <div className="text-xs text-gray-500">
                  {tr("Created", "생성일")}: {new Date(strategy.created_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
