import BacktestConfig from "@/components/backtest/BacktestConfig";
import BenchmarkConfig from "@/components/backtest/BenchmarkConfig";

type StrategyOption = { value: string; label: string };

type BenchmarkConfigItem = {
  symbol: string;
  initialCapital: string;
  commission: string;
  slippage: string;
};

type Props = {
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
  benchmarks: StrategyOption[];
  benchmarkConfigs: BenchmarkConfigItem[];
  onBenchmarkChange: (index: number, value: string) => void;
  onBenchmarkInitialCapitalChange: (index: number, value: string) => void;
  onBenchmarkCommissionChange: (index: number, value: string) => void;
  onBenchmarkSlippageChange: (index: number, value: string) => void;
  onAddBenchmark: () => void;
  onRemoveBenchmark: (index: number) => void;
};

export default function BacktestConfigSection({
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
  onSlippageChange,
  benchmarks,
  benchmarkConfigs,
  onBenchmarkChange,
  onBenchmarkInitialCapitalChange,
  onBenchmarkCommissionChange,
  onBenchmarkSlippageChange,
  onAddBenchmark,
  onRemoveBenchmark,
}: Props) {
  return (
    <>
      <BacktestConfig
        strategies={strategies}
        selectedStrategyIds={selectedStrategyIds}
        onStrategyChange={onStrategyChange}
        onAddStrategy={onAddStrategy}
        onRemoveStrategy={onRemoveStrategy}
        initialCapital={initialCapital}
        onInitialCapitalChange={onInitialCapitalChange}
        commission={commission}
        onCommissionChange={onCommissionChange}
        slippage={slippage}
        onSlippageChange={onSlippageChange}
      />
      <BenchmarkConfig
        benchmarks={benchmarks}
        benchmarkConfigs={benchmarkConfigs}
        onBenchmarkChange={onBenchmarkChange}
        onBenchmarkInitialCapitalChange={onBenchmarkInitialCapitalChange}
        onBenchmarkCommissionChange={onBenchmarkCommissionChange}
        onBenchmarkSlippageChange={onBenchmarkSlippageChange}
        onAddBenchmark={onAddBenchmark}
        onRemoveBenchmark={onRemoveBenchmark}
      />
    </>
  );
}
