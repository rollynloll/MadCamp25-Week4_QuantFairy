import ActivitySection from "@/components/portfolio/ActivitySection";
import AttributionSection from "@/components/portfolio/AttributionSection";
import AllocationCard from "@/components/portfolio/AllocationCard";
import PerformanceSection from "@/components/portfolio/PerformanceSection";
import PortfolioSummary from "@/components/portfolio/PortfolioSummary";
import PositionsTable from "@/components/portfolio/PositionsTable";
import StrategiesTable from "@/components/portfolio/StrategiesTable";
import StrategyEditDrawer from "@/components/portfolio/StrategyEditDrawer";
import { usePortfolioPageData } from "@/hooks/usePortfolio";
import type { Env, Range } from "@/types/portfolio";
import { useState } from "react";
import { rebalancePortfolio } from "@/api/portfolio";

export default function Portfolio() {
  const [env] = useState<Env>("paper");
  const [range, setRange] = useState<Range>("1M");
  const [showBenchmark, setShowBenchmark] = useState(false);

  const [allocationTab, setAllocationTab] = useState<"strategy" | "sector" | "exposure">("strategy");
  const [activityTab, setActivityTab] = useState<"orders" | "trades" | "alerts" | "runs">("orders");

  const [editingStrategy, setEditingStrategy] = useState<string | null>(null);

  const [targetWeights, setTargetWeights] = useState<Record<string, number>>({});
  const [targetCash, setTargetCash] = useState(12.5);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const { data, view, loading, error } = usePortfolioPageData(env, range, showBenchmark);

  if (loading) return <div className="text-gray-400">Lodaing...</div>;
  if (error) return <div className="text-red-400">{error}</div>;
  if (!data || !view) return null;

  const equity = data.summary.account.equity || 0;
  const strategyValueMap = new Map<string, { value: number; count: number }>();
  for (const item of data.positions.items ?? []) {
    const key = item.strategy?.user_strategy_id ?? "unassigned";
    const entry = strategyValueMap.get(key) ?? { value: 0, count: 0 };
    entry.value += item.market_value ?? 0;
    entry.count += 1;
    strategyValueMap.set(key, entry);
  }
  const allocationStrategies = (data.userStrategies?.items ?? []).map((strategy) => {
    const key = strategy.user_strategy_id;
    const entry = strategyValueMap.get(key) ?? { value: 0, count: 0 };
    const currentWeight = equity ? (entry.value / equity) * 100 : 0;
    return {
      id: key,
      name: strategy.name,
      state: strategy.state,
      currentWeight,
      targetWeight: targetWeights[key] ?? currentWeight,
      positionsCount: entry.count || strategy.positions_count || 0,
      lastRun: strategy.last_run_at ?? "-",
    };
  });

  const handleWeightChange = (id: string, value: number) => {
    setTargetWeights({ ...targetWeights, [id]: value });
    setHasUnsavedChanges(true);
  };

  const handleSaveTargets = async () => {
    try {
      const weights = allocationStrategies.reduce<Record<string, number>>((acc, strategy) => {
        acc[strategy.id] = targetWeights[strategy.id] ?? strategy.currentWeight;
        return acc;
      }, {});
      await rebalancePortfolio({
        env,
        mode: "execute",
        target_source: "strategy",
        strategy_ids: allocationStrategies.map((s) => s.id),
        target_weights: weights,
        target_cash_pct: targetCash,
      });
      setHasUnsavedChanges(false);
    } catch (err) {
      console.error(err);
    }
  };

  const handleReset = () => {
    setTargetWeights({});
    setTargetCash(12.5);
    setHasUnsavedChanges(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold">Portfolio</h1>
        <p className="text-sm text-gray-500 mt-1">Current positions, performance, and strategy control</p>
      </div>

      {/* KPI Cards */}
      <PortfolioSummary summary={data.summary} />

      <div className="grid grid-cols-[1fr_400px] gap-6">
        {/* Positions Table */}
        <PositionsTable positions={view.positions} />

        {/* Allocation Card */}
        <AllocationCard
          tab={allocationTab}
          onTabChange={setAllocationTab}
          strategies={allocationStrategies}
          sectorAllocation={view.sectorAllocation}
          targetWeights={targetWeights}
          onTargetWeightChange={handleWeightChange}
          targetCash={targetCash}
          onTargetCashChange={(v) => {
            setTargetCash(v); 
            setHasUnsavedChanges(true);
          }}
          hasUnsavedChanges={hasUnsavedChanges}
          onReset={handleReset}
          onSave={handleSaveTargets}
          showAdvanced={showAdvanced}
          onToggleAdvanced={() => setShowAdvanced(v => !v)}
        />
      </div>

      {/* Performance Section */}
      <PerformanceSection
        equityCurve={view.equityCurve}
        drawdownData={view.drawdownData}
        timeRange={range}
        onTimeRangeChange={(r) => setRange(r as Range)}
        showBenchmark={showBenchmark}
        onShowBenchmarkChange={setShowBenchmark}
      />

      {/* Attribution Section */}
      <AttributionSection attribution={data.attribution} />

      {/* My Strategies Section */}
      <StrategiesTable
        strategies={data.userStrategies?.items ?? []}
        onEdit={(id) => setEditingStrategy(id)}
      />

      {/* Activity Section */}
      <ActivitySection
        tab={activityTab}
        onTabChange={setActivityTab}
        orders={[]}
        alerts={[]}
        botRuns={[]}
      />

      {/* Strategy Edit Drawer */}
      <StrategyEditDrawer
        open={editingStrategy !== null}
        env={env}
        strategyId={editingStrategy}
        strategies={data.userStrategies?.items ?? []}
        onClose={() => setEditingStrategy(null)}
        onSave={() => {
          console.log("Saving strategy settings...");
          setEditingStrategy(null);
        }}
      />
    </div>
  );
}
