import RuleBlock from "./RuleBlock";
import type { BuilderBlock } from "@/types/strategyBuilder";
import { useLanguage } from "@/contexts/LanguageContext";

interface BuilderCanvasProps {
  blocks: BuilderBlock[];
  selectedRuleId: string | null;
  onSelectRule: (ruleId: string) => void;
  onAddRule: (blockId: string) => void;
  onAddCondition: (blockId: string, ruleId: string) => void;
  onRemoveRule: (blockId: string, ruleId: string) => void;
}

export default function BuilderCanvas({
  blocks,
  selectedRuleId,
  onSelectRule,
  onAddRule,
  onAddCondition,
  onRemoveRule,
}: BuilderCanvasProps) {
  const { tr } = useLanguage();

  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded p-4 h-[560px] max-h-[70vh] flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-gray-200">
          {tr("Strategy Builder", "전략 빌더")}
        </h2>
        <span className="text-xs text-gray-500">{tr("Visual blocks", "시각적 블록")}</span>
      </div>

      <div className="flex-1 overflow-auto pr-2 space-y-4">
        {blocks.map((block) => (
          <RuleBlock
            key={block.id}
            block={block}
            selectedRuleId={selectedRuleId}
            onSelectRule={onSelectRule}
            onAddRule={onAddRule}
            onAddCondition={onAddCondition}
            onRemoveRule={onRemoveRule}
          />
        ))}
      </div>
    </div>
  );
}
