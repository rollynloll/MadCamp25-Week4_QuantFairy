import { useLanguage } from "@/contexts/LanguageContext";

type StrategyOption = {
  value: string;
  label: string;
};

export default function BacktestConfig({
  strategies,
  selectedStrategyId,
  onStrategyChange,
  initialCapital,
  onInitialCapitalChange,
  commission,
  onCommissionChange,
  slippage,
  onSlippageChange
}: {
  strategies: StrategyOption[];
  selectedStrategyId: string;
  onStrategyChange: (value: string) => void;
  initialCapital: string;
  onInitialCapitalChange: (value: string) => void;
  commission: string;
  onCommissionChange: (value: string) => void;
  slippage: string;
  onSlippageChange: (value: string) => void;
}) {
  const { tr } = useLanguage();
  const hasStrategies = strategies.length > 0;
  const selectedValue = hasStrategies
    ? strategies.some((strategy) => strategy.value === selectedStrategyId)
      ? selectedStrategyId
      : strategies[0].value
    : "";

  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">{tr("Configuration", "\uC124\uC815")}</h2>
      <div className="grid grid-cols-4 gap-4">
        <div>
          <label className="text-sm text-gray-400 mb-2 block">{tr("Strategy", "\uC804\uB7B5")}</label>
          <select
            className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm"
            value={selectedValue}
            onChange={(event) => onStrategyChange(event.target.value)}
            disabled={!hasStrategies}
          >
            {hasStrategies ? (
              strategies.map((strategy) => (
                <option key={strategy.value} value={strategy.value}>
                  {strategy.label}
                </option>
              ))
            ) : (
              <option value="">{tr("No user strategies", "\uB0B4 \uC804\uB7B5\uC774 \uC5C6\uC2B5\uB2C8\uB2E4")}</option>
            )}
          </select>
        </div>
        <div>
          <label className="text-sm text-gray-400 mb-2 block">
            {tr("Initial Capital", "\uCD08\uAE30 \uC790\uBCF8")}
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
            {tr("Commission", "\uC218\uC218\uB8CC")}
          </label>
          <input
            type="text"
            value={commission}
            onChange={(event) => onCommissionChange(event.target.value)}
            className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm font-mono"
          />
        </div>
        <div>
          <label className="text-sm text-gray-400 mb-2 block">{tr("Slippage", "\uC2AC\uB9AC\uD53C\uC9C0")}</label>
          <input
            type="text"
            value={slippage}
            onChange={(event) => onSlippageChange(event.target.value)}
            className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm font-mono"
          />
        </div>
      </div>
    </div>
  );
}
