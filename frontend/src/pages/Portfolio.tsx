import ActivitySection from "@/components/portfolio/ActivitySection";
import AllocationCard from "@/components/portfolio/AllocationCard";
import PerformanceSection from "@/components/portfolio/PerformanceSection";
import PortfolioSummary from "@/components/portfolio/PortfolioSummary";
import PositionsTable from "@/components/portfolio/PositionsTable";
import StrategiesTable from "@/components/portfolio/StrategiesTable";
import { StrategyEditDrawer } from "@/components/portfolio/StrategyEditDrawer";
import { alerts, botRuns, drawdownData, equityCurve, orders, positions, sectorAllocation, strategies } from "@/data/portfolio.mock";
import { useMemo, useState } from "react";

export default function Portfolio() {
  const [allocationTab, setAllocationTab] = useState<"strategy" | "sector" | "exposure">("strategy");
  const [activityTab, setActivityTab] = useState<"orders" | "trades" | "alerts" | "runs">("orders");
  const [timeRange, setTimeRange] = useState("1M");
  const [showBenchmark, setShowBenchmark] = useState(false);

  const [editingStrategy, setEditingStrategy] = useState<number | null>(null);

  const initialTargets = useMemo(
    () => strategies.reduce((acc, s) => ({ ...acc, [s.id]: s.targetWeight }), {} as Record<number, number>),
    []
  );

  const [targetWeights, setTargetWeights] = useState<Record<number, number>>(initialTargets);
  const [targetCash, setTargetCash] = useState(12.5);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleWeightChange = (id: number, value: number) => {
    setTargetWeights({ ...targetWeights, [id]: value });
    setHasUnsavedChanges(true);
  };

  const handleSaveTargets = () => {
    console.log("Saving targets...", targetWeights, targetCash);
    setHasUnsavedChanges(false);
  };

  const handleReset = () => {
    setTargetWeights(strategies.reduce((acc, s) => ({ ...acc, [s.id]: s.targetWeight }), {}));
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
      <PortfolioSummary />

      {/* Holdings Section */}
      <div className="grid grid-cols-[1fr_400px] gap-6">
        {/* Positions Table */}
        <PositionsTable positions={positions} />

        {/* Allocation Card */}
        <AllocationCard
          tab={allocationTab}
          onTabChange={setAllocationTab}
          strategies={strategies}
          sectorAllocation={sectorAllocation}
          targetWeights={targetWeights}
          onTargetWeightChange={handleWeightChange}
          targetCash={targetCash}
          onTargetCashChange={(v)=>{setTargetCash(v); setHasUnsavedChanges(true);}}
          hasUnsavedChanges={hasUnsavedChanges}
          onReset={handleReset}
          onSave={handleSaveTargets}
          showAdvanced={showAdvanced}
          onToggleAdvanced={()=>setShowAdvanced(v=>!v)}
        />
      </div>

      {/* Performance Section */}
      <PerformanceSection
        equityCurve={equityCurve}
        drawdownData={drawdownData}
        timeRange={timeRange}
        onTimeRangeChange={setTimeRange}
        showBenchmark={showBenchmark}
        onShowBenchmarkChange={setShowBenchmark}
      />

      {/* My Strategies Section */}
      <StrategiesTable
        strategies={strategies}
        onEdit={(id)=>setEditingStrategy(id)}
      />

      {/* Activity Section */}
      <ActivitySection
        tab={activityTab}
        onTabChange={setActivityTab}
        orders={orders}
        alerts={alerts}
        botRuns={botRuns}
      />

      {/* Strategy Edit Drawer */}
      <StrategyEditDrawer
        open={editingStrategy !== null}
        strategyId={editingStrategy}
        strategies={strategies}
        onClose={()=>setEditingStrategy(null)}
        onSave={()=>{ console.log("Saving strategy settings..."); setEditingStrategy(null); }}
      />
    </div>
  );
}