import { strategies } from "@/data/portfolio.mock";
import StateToggle from "./StateToggle";
import { Pause, Play, Settings, Square } from "lucide-react";
import type { Strategy } from "@/types/portfolio";


interface StrategiesProps {
  strategies: Strategy[];
  onEdit: (id: number) => void;
  onStart?: (id: number) => void;
  onPause?: (id: number) => void;
  onStop?: (id: number) => void;
}

export default function StrategiesTable({
  strategies,
  onEdit,
  onStart,
  onPause,
  onStop
}: StrategiesProps) {

  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded">
      <div className="px-4 py-3 border-b border-gray-800">
        <h2 className="font-semibold">My Strategies</h2>
      </div>
      <table className="w-full text-sm">
        <thead className="border-b border-gray-800">
          <tr className="text-xs text-gray-500">
            <th className="text-left py-2 px-4 font-medium">Strategy Name</th>
            <th className="text-left py-2 px-4 font-medium">State</th>
            <th className="text-right py-2 px-4 font-medium">Positions</th>
            <th className="text-left py-2 px-4 font-medium">Last Run</th>
            <th className="text-right py-2 px-4 font-medium">Actions</th>
          </tr>
        </thead>

        <tbody>
          {strategies.map((strategy) => (
            <tr key={strategy.id} className="border-b border-gray-800/50 hover:bg-gray-900/30 transition-colors">
              <td className="py-3 px-4 font-medium">{strategy.name}</td>

              <td className="py-3 px-4">
                <StateToggle state={strategy.state} small />
              </td>

              <td className="text-right py-3 px-4 font-mono">{strategy.positionsCount}</td>

              <td className="py-3 px-4 text-gray-500">{strategy.lastRun}</td>

              <td className="text-right py-3 px-4">
                <div className="flex items-center justify-end gap-2">
                  <button
                    className="p-1.5 hover:bg-gray-800 rounded transition-colors"
                    title="Start"
                    type="button"
                    onClick={() => onStart?.(strategy.id)}
                  >
                    <Play className="w-3.5 h-3.5 text-green-500" />
                  </button>

                  <button
                    className="p-1.5 hover:bg-gray-800 rounded transition-colors"
                    title="Pause"
                    type="button"
                    onClick={() => onPause?.(strategy.id)}
                  >
                    <Pause className="w-3.5 h-3.5 text-yellow-500" />
                  </button>

                  <button
                    className="p-1.5 hover:bg-gray-800 rounded transition-colors"
                    title="Stop"
                    type="button"
                    onClick={() => onStop?.(strategy.id)}
                  >
                    <Square className="w-3.5 h-3.5 text-red-500" />
                  </button>

                  <button
                    onClick={() => onEdit(strategy.id)}
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