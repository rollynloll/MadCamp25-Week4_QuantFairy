import { useMemo, useState } from "react";
import StrategyHeader from "@/components/strategyBuilder/StrategyHeader";
import BuilderCanvas from "@/components/strategyBuilder/BuilderCanvas";
import ConfigPanel from "@/components/strategyBuilder/ConfigPanel";
import BacktestResults from "@/components/strategyBuilder/BacktestResults";
import CodeView from "@/components/strategyBuilder/CodeView";
import type { BuilderBlock, Rule, StrategyKpi, BacktestMetric, TradeLogRow } from "@/types/strategyBuilder";
import { useLanguage } from "@/contexts/LanguageContext";

const initialBlocks: BuilderBlock[] = [
  {
    id: "entry",
    title: "Entry",
    description: "Signals to enter positions",
    rules: [
      {
        id: "entry-1",
        name: "Breakout Entry",
        conditions: ["Price closes above SMA(50)", "Volume above 20D average"],
        action: "Enter long position",
        params: [
          { id: "lookback", label: "Lookback (days)", type: "number", value: 50, min: 5, max: 200, step: 1 },
          { id: "threshold", label: "Signal Threshold", type: "slider", value: 0.7, min: 0, max: 1, step: 0.05 },
          { id: "signal", label: "Signal Type", type: "select", value: "cross_above", options: ["cross_above", "momentum", "breakout"] },
          { id: "confirm_volume", label: "Volume Confirmation", type: "checkbox", value: true },
        ],
      },
    ],
  },
  {
    id: "exit",
    title: "Exit",
    description: "Rules to exit positions",
    rules: [
      {
        id: "exit-1",
        name: "Trailing Stop",
        conditions: ["Price drops 5% from peak"],
        action: "Exit position",
        params: [
          { id: "trail", label: "Trail (%)", type: "number", value: 5, min: 1, max: 20, step: 0.5 },
          { id: "cooldown", label: "Cooldown", type: "select", value: "3d", options: ["1d", "3d", "5d"] },
        ],
      },
    ],
  },
  {
    id: "portfolio",
    title: "Portfolio",
    description: "Position sizing & allocation",
    rules: [
      {
        id: "portfolio-1",
        name: "Equal Weight",
        conditions: ["Top-K selected"],
        action: "Equal weight across positions",
        params: [
          { id: "top_k", label: "Top K", type: "number", value: 10, min: 3, max: 50, step: 1 },
          { id: "max_positions", label: "Max Positions", type: "slider", value: 12, min: 2, max: 20, step: 1 },
          { id: "weighting", label: "Weighting", type: "select", value: "equal", options: ["equal", "inverse_vol", "score"] },
        ],
      },
    ],
  },
  {
    id: "risk",
    title: "Risk",
    description: "Portfolio risk controls",
    rules: [
      {
        id: "risk-1",
        name: "Drawdown Guard",
        conditions: ["Daily drawdown > 2%"],
        action: "Reduce exposure to cash",
        params: [
          { id: "max_dd", label: "Max DD (%)", type: "number", value: 2, min: 0.5, max: 10, step: 0.5 },
          { id: "halt", label: "Halt Trading", type: "checkbox", value: false },
          { id: "recovery", label: "Recovery Window", type: "select", value: "5d", options: ["3d", "5d", "10d"] },
        ],
      },
    ],
  },
];

const mockKpis: StrategyKpi[] = [
  { label: "Sharpe", value: "1.42" },
  { label: "CAGR", value: "18.3%" },
  { label: "Max DD", value: "-7.8%" },
];

const mockMetrics: BacktestMetric[] = [
  { label: "CAGR", value: "18.3%" },
  { label: "Sharpe", value: "1.42" },
  { label: "MDD", value: "-7.8%" },
  { label: "Win Rate", value: "56%" },
  { label: "Trades", value: "124" },
  { label: "Turnover", value: "32%" },
];

const mockTrades: TradeLogRow[] = [
  { id: "t1", time: "2026-02-01", symbol: "AAPL", side: "BUY", qty: 12, price: 192.4, pnl: 14.2 },
  { id: "t2", time: "2026-02-03", symbol: "NVDA", side: "BUY", qty: 8, price: 680.1, pnl: -8.6 },
  { id: "t3", time: "2026-02-05", symbol: "MSFT", side: "SELL", qty: 6, price: 412.5, pnl: 24.1 },
];

function generatePython(blocks: BuilderBlock[]) {
  const lines: string[] = [];
  lines.push("def compute_target_weights(prices, ctx, universe, dt):");
  lines.push("    \"\"\"Auto-generated template from visual rules.\"\"\"");
  blocks.forEach((block) => {
    lines.push(`    # ${block.title}`);
    block.rules.forEach((rule) => {
      const conditions = rule.conditions.join(" AND ") || "<no conditions>";
      lines.push(`    # IF ${conditions} THEN ${rule.action}`);
    });
  });
  lines.push("    return {}");
  return lines.join("\n");
}

export default function StrategyPage() {
  const { tr } = useLanguage();
  const [name, setName] = useState("Momentum Lab Strategy");
  const [description, setDescription] = useState("Cross-sectional momentum with risk guardrails.");
  const [liveEnabled, setLiveEnabled] = useState(false);
  const [activeTab, setActiveTab] = useState<"visual" | "code">("visual");
  const [blocks, setBlocks] = useState<BuilderBlock[]>(initialBlocks);
  const [selectedRuleId, setSelectedRuleId] = useState<string | null>(initialBlocks[0].rules[0].id);

  const selectedRule = useMemo(() => {
    for (const block of blocks) {
      const found = block.rules.find((rule) => rule.id === selectedRuleId);
      if (found) return found;
    }
    return null;
  }, [blocks, selectedRuleId]);

  const handleAddRule = (blockId: string) => {
    setBlocks((prev) =>
      prev.map((block) => {
        if (block.id !== blockId) return block;
        const nextIndex = block.rules.length + 1;
        const newRule: Rule = {
          id: `${blockId}-${nextIndex}-${Date.now()}`,
          name: `${block.title} Rule ${nextIndex}`,
          conditions: [tr("New condition", "새 조건")],
          action: tr("Define action", "액션 정의"),
          params: [
            { id: "threshold", label: "Threshold", type: "number", value: 1, min: 0, max: 10, step: 0.5 },
            { id: "enabled", label: "Enabled", type: "checkbox", value: true },
          ],
        };
        return { ...block, rules: [...block.rules, newRule] };
      })
    );
  };

  const handleAddCondition = (blockId: string, ruleId: string) => {
    setBlocks((prev) =>
      prev.map((block) => {
        if (block.id !== blockId) return block;
        return {
          ...block,
          rules: block.rules.map((rule) => {
            if (rule.id !== ruleId) return rule;
            const next = rule.conditions.length + 1;
            return { ...rule, conditions: [...rule.conditions, `${tr("Condition", "조건")} ${next}`] };
          }),
        };
      })
    );
  };

  const handleRemoveRule = (blockId: string, ruleId: string) => {
    setBlocks((prev) =>
      prev.map((block) => {
        if (block.id !== blockId) return block;
        const nextRules = block.rules.filter((rule) => rule.id !== ruleId);
        return { ...block, rules: nextRules };
      })
    );
    if (selectedRuleId === ruleId) {
      setSelectedRuleId(null);
    }
  };

  const handleParamChange = (ruleId: string, paramId: string, value: number | string | boolean) => {
    setBlocks((prev) =>
      prev.map((block) => ({
        ...block,
        rules: block.rules.map((rule) => {
          if (rule.id !== ruleId) return rule;
          return {
            ...rule,
            params: rule.params.map((param) =>
              param.id === paramId ? { ...param, value } : param
            ),
          };
        }),
      }))
    );
  };

  const pythonCode = useMemo(() => generatePython(blocks), [blocks]);

  return (
    <div className="space-y-6">
      <StrategyHeader
        name={name}
        description={description}
        onNameChange={setName}
        onDescriptionChange={setDescription}
        onSave={() => console.log("save")}
        onRun={() => console.log("run backtest")}
        liveEnabled={liveEnabled}
        onToggleLive={() => setLiveEnabled((v) => !v)}
        kpis={mockKpis}
      />

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setActiveTab("visual")}
          className={`px-3 py-1.5 rounded border text-xs font-medium ${
            activeTab === "visual"
              ? "border-blue-500 text-white bg-blue-500/10"
              : "border-gray-800 text-gray-400 hover:text-gray-200"
          }`}
        >
          {tr("Visual Builder", "비주얼 빌더")}
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("code")}
          className={`px-3 py-1.5 rounded border text-xs font-medium ${
            activeTab === "code"
              ? "border-blue-500 text-white bg-blue-500/10"
              : "border-gray-800 text-gray-400 hover:text-gray-200"
          }`}
        >
          {tr("Code", "코드")}
        </button>
      </div>

      {activeTab === "visual" ? (
        <div className="grid grid-cols-1 xl:grid-cols-[7fr_3fr] gap-6">
          <BuilderCanvas
            blocks={blocks}
            selectedRuleId={selectedRuleId}
            onSelectRule={setSelectedRuleId}
            onAddRule={handleAddRule}
            onAddCondition={handleAddCondition}
            onRemoveRule={handleRemoveRule}
          />
          <ConfigPanel selectedRule={selectedRule} onParamChange={handleParamChange} />
        </div>
      ) : (
        <CodeView code={pythonCode} />
      )}

      <BacktestResults metrics={mockMetrics} trades={mockTrades} />
    </div>
  );
}
