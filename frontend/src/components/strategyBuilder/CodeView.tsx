import { useLanguage } from "@/contexts/LanguageContext";

interface CodeViewProps {
  code: string;
}

export default function CodeView({ code }: CodeViewProps) {
  const { tr } = useLanguage();
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-gray-200">
          {tr("Auto-generated Python", "자동 생성된 Python")}
        </h2>
        <span className="text-xs text-gray-500">{tr("Read-only", "읽기 전용")}</span>
      </div>
      <textarea
        readOnly
        value={code}
        className="w-full h-[520px] bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 font-mono text-xs text-gray-200"
      />
    </div>
  );
}
