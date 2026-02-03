import type { BuilderBlock } from "@/types/strategyBuilder";
import { useLanguage } from "@/contexts/LanguageContext";

interface RuleBlockProps {
  block: BuilderBlock;
  selectedRuleId: string | null;
  onSelectRule: (ruleId: string) => void;
  onAddRule: (blockId: string) => void;
  onAddCondition: (blockId: string, ruleId: string) => void;
  onRemoveRule: (blockId: string, ruleId: string) => void;
}

export default function RuleBlock({
  block,
  selectedRuleId,
  onSelectRule,
  onAddRule,
  onAddCondition,
  onRemoveRule,
}: RuleBlockProps) {
  const { tr } = useLanguage();

  return (
    <div className="rounded-lg border border-gray-800 bg-[#0a0d14] p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-sm font-semibold text-gray-200">{block.title}</div>
          <div className="text-xs text-gray-500">{block.description}</div>
        </div>
        <button
          type="button"
          onClick={() => onAddRule(block.id)}
          className="text-xs px-2 py-1 rounded border border-gray-700 text-gray-300 hover:text-white"
        >
          {tr("Add Rule", "규칙 추가")}
        </button>
      </div>

      <div className="space-y-3">
        {block.rules.map((rule) => {
          const isSelected = selectedRuleId === rule.id;
          const conditionText = rule.conditions.length
            ? rule.conditions.join(" AND ")
            : tr("<empty condition>", "<조건 없음>");
          return (
            <div
              key={rule.id}
              onClick={() => onSelectRule(rule.id)}
              className={`rounded border p-3 cursor-pointer transition-colors ${
                isSelected
                  ? "border-blue-500 bg-blue-500/10"
                  : "border-gray-800 bg-gray-900/40 hover:border-gray-700"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="text-xs font-semibold text-gray-300">{rule.name}</div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemoveRule(block.id, rule.id);
                  }}
                  className="text-[11px] text-gray-500 hover:text-red-400"
                >
                  {tr("Remove", "삭제")}
                </button>
              </div>
              <div className="mt-2 text-xs text-gray-400">
                <span className="text-blue-400">IF</span> {conditionText}
                <span className="text-blue-400"> THEN</span> {rule.action}
              </div>
              <div className="mt-3 flex items-center gap-2">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onAddCondition(block.id, rule.id);
                  }}
                  className="text-[11px] px-2 py-1 rounded border border-gray-700 text-gray-300 hover:text-white"
                >
                  {tr("Add Condition", "조건 추가")}
                </button>
                <span className="text-[11px] text-gray-500">
                  {tr("Select to edit parameters", "선택 후 파라미터 편집")}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
