import ActivitySection from "@/components/portfolio/ActivitySection";
import AllocationCard from "@/components/portfolio/AllocationCard";
import PortfolioSummary from "@/components/portfolio/PortfolioSummary";
import StrategiesTable from "@/components/portfolio/StrategiesTable";
import StrategyEditDrawer from "@/components/portfolio/StrategyEditDrawer";
import { usePortfolioPageData } from "@/hooks/usePortfolio";
import type { AlertItem, BotRun, Env, Order, Range, StrategyState, UserStrategyListItem } from "@/types/portfolio";
import { useState } from "react";
import { rebalancePortfolio } from "@/api/portfolio";
import { setUserStrategyState } from "@/api/userStrategies";
import { useLanguage } from "@/contexts/LanguageContext";

export default function Portfolio() {
  const { tr } = useLanguage();
  const [env] = useState<Env>("paper");
  const [range] = useState<Range>("1M");
  const [showBenchmark] = useState(false);

  const [allocationTab, setAllocationTab] = useState<"strategy" | "sector" | "exposure">("strategy");
  const [activityTab, setActivityTab] = useState<"orders" | "trades" | "alerts" | "runs">("orders");

  const [editingStrategy, setEditingStrategy] = useState<string | null>(null);
  const [strategyStateOverrides, setStrategyStateOverrides] = useState<Record<string, StrategyState>>({});
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const [targetWeights, setTargetWeights] = useState<Record<string, number>>({});
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const { data, view, loading, error, loadActivity } = usePortfolioPageData(env, range, showBenchmark);

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
  const resolvedStrategies: UserStrategyListItem[] = (data.userStrategies?.items ?? []).map(
    (strategy) => ({
      ...strategy,
      state: strategyStateOverrides[strategy.user_strategy_id] ?? strategy.state,
    })
  );

  const allocationStrategies = resolvedStrategies
    .filter((strategy) => strategy.state !== "stopped")
    .map((strategy) => {
    const key = strategy.user_strategy_id;
    const entry = strategyValueMap.get(key) ?? { value: 0, count: 0 };
    const currentWeight = equity ? (entry.value / equity) * 100 : 0;
    return {
      id: key,
      name: strategy.name,
      state: strategy.state,
      currentWeight,
      targetWeight:
        strategy.state === "paused"
          ? currentWeight
          : (targetWeights[key] ?? currentWeight),
      positionsCount: entry.count || strategy.positions_count || 0,
      lastRun: strategy.last_run_at ?? "-",
    };
  });

  const activityItems = data.activity?.items ?? [];
  const orders: Order[] = activityItems
    .filter((item) => item.type === "order")
    .map((item, index) => {
      const sideRaw = String(item.data?.side ?? "buy").toUpperCase();
      const statusRaw = String(item.data?.status ?? "pending").toLowerCase();
      const status: Order["status"] =
        statusRaw === "filled" || statusRaw === "partial" || statusRaw === "cancelled"
          ? (statusRaw as Order["status"])
          : "pending";
      return {
        id: Number(item.id) || index,
        time: item.t,
        type: sideRaw === "SELL" ? "SELL" : "BUY",
        symbol: String(item.data?.symbol ?? "-"),
        qty: Number(item.data?.qty ?? 0),
        status,
        strategy: String(item.data?.user_strategy_id ?? "-"),
      };
    });
  const alerts: AlertItem[] = activityItems
    .filter((item) => item.type === "alert")
    .map((item, index) => ({
      id: Number(item.id) || index,
      time: item.t,
      level: item.data?.severity === "error" ? "error" : "warning",
      message: item.data?.message ?? item.data?.title ?? "Alert",
      strategy: String(item.data?.user_strategy_id ?? "-"),
    }));
  const botRuns: BotRun[] = activityItems
    .filter((item) => item.type === "bot_run")
    .map((item, index) => ({
      id: Number(item.id) || index,
      time: item.t,
      status: item.data?.status === "failed" ? "failed" : "success",
      duration: String(item.data?.duration ?? "-"),
      trades: Number(item.data?.trades ?? 0),
    }));

  const resolveCurrentWeight = (strategyId: string) => {
    const entry = strategyValueMap.get(strategyId);
    return equity ? ((entry?.value ?? 0) / equity) * 100 : 0;
  };

  const handleWeightChange = (id: string, value: number) => {
    setTargetWeights({ ...targetWeights, [id]: value });
    setHasUnsavedChanges(true);
    setSaveError(null);
    setSaveStatus(null);
  };

  const totalTarget = allocationStrategies.reduce((sum, strategy) => sum + strategy.targetWeight, 0);
  const derivedCash = Math.max(0, 100 - totalTarget);

  const handleSaveTargets = async () => {
    try {
      if (totalTarget > 100) {
        setSaveError("Total target exceeds 100%");
        return;
      }
      if (allocationStrategies.length === 0) {
        setSaveError("No active strategies to rebalance");
        return;
      }
      setSaveStatus(tr("Saving...", "저장 중..."));
      setIsSaving(true);
      setSaveError(null);
      const weights = allocationStrategies.reduce<Record<string, number>>((acc, strategy) => {
        acc[strategy.id] = strategy.targetWeight;
        return acc;
      }, {});
      await rebalancePortfolio({
        env,
        mode: "execute",
        target_source: "strategy",
        strategy_ids: allocationStrategies.map((s) => s.id),
        target_weights: weights,
        target_cash_pct: derivedCash,
        allow_new_positions: true,
      });
      setHasUnsavedChanges(false);
      const timeLabel = new Date().toLocaleTimeString("ko-KR", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
      setSaveStatus(tr(`Saved at ${timeLabel}`, `${timeLabel} 저장 완료`));
      setTimeout(() => setSaveStatus(null), 3000);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to save targets";
      setSaveError(message);
      setSaveStatus(tr("Save failed", "저장 실패"));
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleStrategyAction = async (id: string, action: "start" | "pause" | "stop") => {
    const baseState =
      resolvedStrategies.find((strategy) => strategy.user_strategy_id === id)?.state ?? "stopped";
    const prevOverride = strategyStateOverrides[id];
    const nextState: StrategyState =
      action === "start" ? "running" : action === "pause" ? "paused" : "stopped";

    setStrategyStateOverrides((prev) => ({ ...prev, [id]: nextState }));
    if (action === "pause") {
      const currentWeight = resolveCurrentWeight(id);
      setTargetWeights((prev) => ({ ...prev, [id]: currentWeight }));
    }
    if (action === "stop") {
      setTargetWeights((prev) => {
        const { [id]: _, ...rest } = prev;
        return rest;
      });
    }

    try {
      await setUserStrategyState(env, id, action);
    } catch (err) {
      setStrategyStateOverrides((prev) => {
        if (prevOverride === undefined) {
          const { [id]: _, ...rest } = prev;
          return rest;
        }
        return { ...prev, [id]: baseState };
      });
      console.error(err);
    }
  };

  const handleReset = () => {
    setTargetWeights({});
    setHasUnsavedChanges(false);
    setSaveError(null);
    setSaveStatus(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold">{tr("Portfolio", "포트폴리오")}</h1>
        <p className="text-sm text-gray-500 mt-1">
          {tr("Current positions, performance, and strategy control", "보유 종목 수, 성과 및 전략 관리")}
        </p>
      </div>

      {/* KPI Cards */}
      <PortfolioSummary summary={data.summary} />

      <div className="bg-[#0d1117] border border-gray-800 rounded p-4 text-sm text-gray-300">
        Rebalancing settings are applied at the <span className="text-white font-semibold">next scheduled rebalance</span>.
        Adjust strategy weights and sector focus. Cash is auto-calculated from the remaining allocation.
      </div>

      {/* Allocation Card */}
      <AllocationCard
        tab={allocationTab}
        onTabChange={setAllocationTab}
        strategies={allocationStrategies}
        sectorAllocation={view.sectorAllocation}
        targetWeights={targetWeights}
        onTargetWeightChange={handleWeightChange}
        derivedCash={derivedCash}
        totalTarget={totalTarget}
        hasUnsavedChanges={hasUnsavedChanges}
        onReset={handleReset}
        onSave={handleSaveTargets}
        showAdvanced={showAdvanced}
        onToggleAdvanced={() => setShowAdvanced(v => !v)}
        saveError={saveError}
        isSaving={isSaving}
        saveStatus={saveStatus}
      />

      {/* My Strategies Section */}
      <StrategiesTable
        strategies={resolvedStrategies}
        onEdit={(id) => setEditingStrategy(id)}
        onStart={(id) => handleStrategyAction(id, "start")}
        onPause={(id) => handleStrategyAction(id, "pause")}
        onStop={(id) => handleStrategyAction(id, "stop")}
      />

      {/* Activity Section */}
      <ActivitySection
        tab={activityTab}
        onTabChange={(tab) => {
          setActivityTab(tab);
          loadActivity();
        }}
        orders={orders}
        alerts={alerts}
        botRuns={botRuns}
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
