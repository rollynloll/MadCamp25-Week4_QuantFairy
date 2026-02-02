import StateToggle from "./StateToggle";
import { Pause, Play, Settings, Square } from "lucide-react";
import type { UserStrategyListItem } from "@/types/portfolio";
import { useLanguage } from "@/contexts/LanguageContext";


interface StrategiesProps {
  strategies: UserStrategyListItem[];
  onEdit: (id: string) => void;
  onStart?: (id: string) => void;
  onPause?: (id: string) => void;
  onStop?: (id: string) => void;
}

export default function StrategiesTable({
  strategies,
  onEdit,
  onStart,
  onPause,
  onStop
}: StrategiesProps) {
  const { tr } = useLanguage();

  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded">
      <div className="px-4 py-3 border-b border-gray-800">
        <h2 className="font-semibold">{tr("My Strategies", "내 전략")}</h2>
      </div>
      <table className="w-full text-sm">
        <thead className="border-b border-gray-800">
          <tr className="text-xs text-gray-500">
            <th className="text-left py-2 px-4 font-medium">{tr("Strategy Name", "전략 이름")}</th>
            <th className="text-left py-2 px-4 font-medium">{tr("State", "상태")}</th>
            <th className="text-right py-2 px-4 font-medium">{tr("Positions", "포지션")}</th>
            <th className="text-left py-2 px-4 font-medium">{tr("Last Run", "최근 실행")}</th>
            <th className="text-right py-2 px-4 font-medium">{tr("Actions", "액션")}</th>
          </tr>
        </thead>

        <tbody>
          {strategies.map((strategy) => (
            <tr
              key={strategy.user_strategy_id}
              className="border-b border-gray-800/50 hover:bg-gray-900/30 transition-colors"
            >
              <td className="py-3 px-4 font-medium">{strategy.name}</td>

              <td className="py-3 px-4">
                <StateToggle state={strategy.state} small />
              </td>

              <td className="text-right py-3 px-4 font-mono">{strategy.positions_count}</td>

              <td className="py-3 px-4 text-gray-500">
                {strategy.last_run_at
                  ? new Date(strategy.last_run_at).toLocaleString()
                  : "-"}
              </td>

              <td className="text-right py-3 px-4">
                <div className="flex items-center justify-end gap-2">
                  <button
                    className="p-1.5 hover:bg-gray-800 rounded transition-colors"
                    title="Start"
                    type="button"
                    onClick={() => onStart?.(strategy.user_strategy_id)}
                  >
                    <Play className="w-3.5 h-3.5 text-green-500" />
                  </button>

                  <button
                    className="p-1.5 hover:bg-gray-800 rounded transition-colors"
                    title="Pause"
                    type="button"
                    onClick={() => onPause?.(strategy.user_strategy_id)}
                  >
                    <Pause className="w-3.5 h-3.5 text-yellow-500" />
                  </button>

                  <button
                    className="p-1.5 hover:bg-gray-800 rounded transition-colors"
                    title="Stop"
                    type="button"
                    onClick={() => onStop?.(strategy.user_strategy_id)}
                  >
                    <Square className="w-3.5 h-3.5 text-red-500" />
                  </button>

                  <button
                    onClick={() => onEdit(strategy.user_strategy_id)}
                    className="p-1.5 hover:bg-gray-800 rounded transition-colors"
                    title="Edit"
                    type="button"
                  >
                    <Settings className="w-3.5 h-3.5 text-blue-500" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
