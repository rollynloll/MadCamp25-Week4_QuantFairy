import type { Rule } from "@/types/strategyBuilder";
import { useLanguage } from "@/contexts/LanguageContext";

interface ConfigPanelProps {
  selectedRule: Rule | null;
  onParamChange: (ruleId: string, paramId: string, value: number | string | boolean) => void;
}

export default function ConfigPanel({ selectedRule, onParamChange }: ConfigPanelProps) {
  const { tr } = useLanguage();

  if (!selectedRule) {
    return (
      <div className="bg-[#0d1117] border border-gray-800 rounded p-4 h-[560px] max-h-[70vh]">
        <div className="text-sm font-semibold text-gray-200 mb-2">
          {tr("Config Panel", "설정 패널")}
        </div>
        <div className="text-xs text-gray-500">
          {tr("Select a rule to edit parameters.", "규칙을 선택하면 파라미터를 수정할 수 있습니다.")}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded p-4 h-[560px] max-h-[70vh] overflow-auto">
      <div className="mb-4">
        <div className="text-sm font-semibold text-gray-200">{selectedRule.name}</div>
        <div className="text-xs text-gray-500 mt-1">
          {tr("Rule settings", "규칙 설정")}
        </div>
      </div>

      <div className="space-y-4">
        {selectedRule.params.map((param) => (
          <div key={param.id} className="space-y-2">
            <label className="text-xs text-gray-400">{param.label}</label>
            {param.type === "number" && (
              <input
                type="number"
                value={param.value as number}
                min={param.min}
                max={param.max}
                step={param.step ?? 1}
                onChange={(e) => onParamChange(selectedRule.id, param.id, Number(e.target.value))}
                className="w-full bg-[#0a0d14] border border-gray-800 rounded px-2 py-1 text-xs"
              />
            )}
            {param.type === "select" && (
              <select
                value={String(param.value)}
                onChange={(e) => onParamChange(selectedRule.id, param.id, e.target.value)}
                className="w-full bg-[#0a0d14] border border-gray-800 rounded px-2 py-1 text-xs"
              >
                {(param.options ?? []).map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            )}
            {param.type === "slider" && (
              <div className="space-y-2">
                <input
                  type="range"
                  value={param.value as number}
                  min={param.min}
                  max={param.max}
                  step={param.step ?? 1}
                  onChange={(e) => onParamChange(selectedRule.id, param.id, Number(e.target.value))}
                  className="w-full accent-blue-500"
                />
                <div className="text-xs text-gray-500">
                  {param.value}
                </div>
              </div>
            )}
            {param.type === "checkbox" && (
              <label className="flex items-center gap-2 text-xs text-gray-300">
                <input
                  type="checkbox"
                  checked={Boolean(param.value)}
                  onChange={(e) => onParamChange(selectedRule.id, param.id, e.target.checked)}
                  className="h-4 w-4 rounded border-gray-700 bg-gray-900 text-blue-500"
                />
                {tr("Enabled", "활성화")}
              </label>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
