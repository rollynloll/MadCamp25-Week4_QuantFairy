import { useLanguage } from "@/contexts/LanguageContext";

type BenchmarkOption = {
  value: string;
  label: string;
};

export default function BenchmarkConfig({
  benchmarks,
  benchmarkConfigs,
  onBenchmarkChange,
  onBenchmarkInitialCapitalChange,
  onBenchmarkCommissionChange,
  onBenchmarkSlippageChange,
  onAddBenchmark,
  onRemoveBenchmark
}: {
  benchmarks: BenchmarkOption[];
  benchmarkConfigs: {
    symbol: string;
    initialCapital: string;
    commission: string;
    slippage: string;
  }[];
  onBenchmarkChange: (index: number, value: string) => void;
  onBenchmarkInitialCapitalChange: (index: number, value: string) => void;
  onBenchmarkCommissionChange: (index: number, value: string) => void;
  onBenchmarkSlippageChange: (index: number, value: string) => void;
  onAddBenchmark: () => void;
  onRemoveBenchmark: (index: number) => void;
}) {
  const { tr } = useLanguage();
  const hasBenchmarks = benchmarks.length > 0;
  const resolvedConfigs = benchmarkConfigs.length
    ? benchmarkConfigs
    : [
        {
          symbol: hasBenchmarks ? benchmarks[0].value : "",
          initialCapital: "",
          commission: "",
          slippage: ""
        }
      ];

  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">{tr("Benchmark", "벤치마크")}</h2>
        <button
          type="button"
          className="text-xs text-gray-300 border border-gray-800 px-2 py-1 rounded hover:text-white hover:border-gray-600 transition-colors disabled:opacity-50"
          onClick={onAddBenchmark}
          disabled={!hasBenchmarks}
        >
          + {tr("Add Benchmark", "벤치마크 추가")}
        </button>
      </div>
      <div className="grid grid-cols-4 gap-4">
        {resolvedConfigs.map((config, index) => (
          <div key={`${config.symbol}-${index}`} className="col-span-4 grid grid-cols-4 gap-4">
            <div>
              <label className="text-sm text-gray-400 mb-2 block">
                {tr("Benchmark", "벤치마크")} {index + 1}
              </label>
              <div className="flex gap-2">
                <select
                  className="flex-1 bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm"
                  value={config.symbol}
                  onChange={(event) => onBenchmarkChange(index, event.target.value)}
                  disabled={!hasBenchmarks}
                >
                  {hasBenchmarks ? (
                    benchmarks.map((benchmark) => (
                      <option key={benchmark.value} value={benchmark.value}>
                        {benchmark.label}
                      </option>
                    ))
                  ) : (
                    <option value="">{tr("No benchmarks", "벤치마크 없음")}</option>
                  )}
                </select>
                <button
                  type="button"
                  className="text-xs text-gray-300 border border-gray-800 px-2 rounded hover:text-white hover:border-gray-600 transition-colors disabled:opacity-50"
                  onClick={() => onRemoveBenchmark(index)}
                  disabled={resolvedConfigs.length <= 1}
                >
                  {tr("Remove", "삭제")}
                </button>
              </div>
            </div>
            <div>
              <label className="text-sm text-gray-400 mb-2 block">
                {tr("Initial Capital", "초기 자본")}
              </label>
              <input
                type="text"
                value={config.initialCapital}
                onChange={(event) => onBenchmarkInitialCapitalChange(index, event.target.value)}
                className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm font-mono"
              />
            </div>
            <div>
              <label className="text-sm text-gray-400 mb-2 block">
                {tr("Commission", "수수료")}
              </label>
              <input
                type="text"
                value={config.commission}
                onChange={(event) => onBenchmarkCommissionChange(index, event.target.value)}
                className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm font-mono"
              />
            </div>
            <div>
              <label className="text-sm text-gray-400 mb-2 block">
                {tr("Slippage", "슬리피지")}
              </label>
              <input
                type="text"
                value={config.slippage}
                onChange={(event) => onBenchmarkSlippageChange(index, event.target.value)}
                className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm font-mono"
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}