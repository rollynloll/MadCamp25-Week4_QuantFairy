import type { BacktestConfigData } from "@/types/backtest";

export default function BacktestConfig({ config }: { config: BacktestConfigData }) {
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">Configuration</h2>
      <div className="grid grid-cols-4 gap-4">
        <div>
          <label className="text-sm text-gray-400 mb-2 block">Strategy</label>
          <select className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm">
            <option>{config.strategy}</option>
            <option>Momentum Breakout</option>
            <option>Pairs Trading</option>
          </select>
        </div>
        <div>
          <label className="text-sm text-gray-400 mb-2 block">
            Initial Capital
          </label>
          <input
            type="text"
            defaultValue={config.initialCapital}
            className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm font-mono"
          />
        </div>
        <div>
          <label className="text-sm text-gray-400 mb-2 block">
            Commission
          </label>
          <input
            type="text"
            defaultValue={config.commission}
            className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm font-mono"
          />
        </div>
        <div>
          <label className="text-sm text-gray-400 mb-2 block">Slippage</label>
          <input
            type="text"
            defaultValue={config.slippage}
            className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm font-mono"
          />
        </div>
      </div>
    </div>
  );
}