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
import { useLanguage } from "@/contexts/LanguageContext";

export default function Portfolio() {
  const [env] = useState<Env>("paper");
  const [range, setRange] = useState<Range>("1M");
  const [showBenchmark, setShowBenchmark] = useState(false);

  const [allocationTab, setAllocationTab] = useState<"strategy" | "sector" | "exposure">("strategy");
  const [activityTab, setActivityTab] = useState<"orders" | "trades" | "alerts" | "runs">("orders");

  const [editingStrategy, setEditingStrategy] = useState<string | null>(null);

  const [targetWeights, setTargetWeights] = useState<Record<number, number>>({});
  const [targetCash, setTargetCash] = useState(12.5);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const { data, view, loading, error } = usePortfolioPageData(env, range, showBenchmark);
  const { tr } = useLanguage();

  if (loading) return <div className="text-sm text-gray-400">{tr("Loading Portfolio...", "포트폴리오 불러오는 중...")}</div>;
  if (error) return <div className="text-red-400">{error}</div>;
  if (!data || !view) return null;

  const handleWeightChange = (id: number, value: number) => {
    setTargetWeights({ ...targetWeights, [id]: value });
    setHasUnsavedChanges(true);
  };

  const handleSaveTargets = () => {
    console.log("Saving targets...", targetWeights, targetCash);
    setHasUnsavedChanges(false);
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
        <h1 className="text-2xl font-semibold">{tr("Portfolio", "포트폴리오")}</h1>
        <p className="text-sm text-gray-500 mt-1">
          {tr("Current positions, performance, and strategy control", "현재 포지션, 성과, 전략 제어")}
        </p>
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
          strategies={[]}
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
        strategies={[]}
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
        strategies={[]}
        onClose={() => setEditingStrategy(null)}
        onSave={() => { 
          console.log("Saving strategy settings..."); 
          setEditingStrategy(null); 
        }}
      />
    </div>
  );
}
