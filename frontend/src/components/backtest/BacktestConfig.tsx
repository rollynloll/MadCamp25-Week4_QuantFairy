type StrategyOption = {
  value: string;
  label: string;
};

export default function BacktestConfig({
  strategies,
  selectedStrategyIds,
  onStrategyChange,
  onAddStrategy,
  onRemoveStrategy,
  initialCapital,
  onInitialCapitalChange,
  commission,
  onCommissionChange,
  slippage,
  onSlippageChange
}: {
  strategies: StrategyOption[];
  selectedStrategyIds: string[];
  onStrategyChange: (index: number, value: string) => void;
  onAddStrategy: () => void;
  onRemoveStrategy: (index: number) => void;
  initialCapital: string;
  onInitialCapitalChange: (value: string) => void;
  commission: string;
  onCommissionChange: (value: string) => void;
  slippage: string;
  onSlippageChange: (value: string) => void;
}) {
  const hasStrategies = strategies.length > 0;
  const selectedValues = selectedStrategyIds.length
    ? selectedStrategyIds.map((value) =>
        strategies.some((strategy) => strategy.value === value)
          ? value
          : strategies[0]?.value ?? ""
      )
    : hasStrategies
      ? [strategies[0].value]
      : [""];

  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Configuration</h2>
        <button
          type="button"
          className="text-xs text-gray-300 border border-gray-800 px-2 py-1 rounded hover:text-white hover:border-gray-600 transition-colors disabled:opacity-50"
          onClick={onAddStrategy}
          disabled={!hasStrategies}
        >
          + Add Strategy
        </button>
      </div>
      <div className="space-y-4">
        <div className="grid grid-cols-4 gap-4">
          {selectedValues.map((value, index) => (
            <div key={`${value}-${index}`} className="col-span-4 grid grid-cols-4 gap-4">
              <div className="col-span-3">
                <label className="text-sm text-gray-400 mb-2 block">
                  Strategy {index + 1}
                </label>
                <select
                  className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm"
                  value={value}
                  onChange={(event) => onStrategyChange(index, event.target.value)}
                  disabled={!hasStrategies}
                >
                  {hasStrategies ? (
                    strategies.map((strategy) => (
                      <option key={strategy.value} value={strategy.value}>
                        {strategy.label}
                      </option>
                    ))
                  ) : (
                    <option value="">No user strategies</option>
                  )}
                </select>
              </div>
              <div className="col-span-1 flex items-end">
                <button
                  type="button"
                  className="w-full text-xs text-gray-300 border border-gray-800 px-2 py-2 rounded hover:text-white hover:border-gray-600 transition-colors disabled:opacity-50"
                  onClick={() => onRemoveStrategy(index)}
                  disabled={selectedValues.length <= 1}
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-4 gap-4">
        <div>
          <label className="text-sm text-gray-400 mb-2 block">
            Initial Capital
          </label>
          <input
            type="text"
            value={initialCapital}
            onChange={(event) => onInitialCapitalChange(event.target.value)}
            className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm font-mono"
          />
        </div>
        <div>
          <label className="text-sm text-gray-400 mb-2 block">
            Commission
          </label>
          <input
            type="text"
            value={commission}
            onChange={(event) => onCommissionChange(event.target.value)}
            className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm font-mono"
          />
        </div>
        <div>
          <label className="text-sm text-gray-400 mb-2 block">Slippage</label>
          <input
            type="text"
            value={slippage}
            onChange={(event) => onSlippageChange(event.target.value)}
            className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm font-mono"
          />
        </div>
        </div>
      </div>
    </div>
  );
}
