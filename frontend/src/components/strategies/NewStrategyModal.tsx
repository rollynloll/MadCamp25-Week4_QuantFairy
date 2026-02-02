import { useState } from "react";
import { useLanguage } from "@/contexts/LanguageContext";

interface NewStrategyModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (body: { 
    name: string;
    params: Record<string, any>;
    note?: string
  }) => void;
  loading?: boolean;
  error?: string | null;
}

export default function NewStrategyModal({
  open,
  onClose,
  onSubmit,
  loading = false,
  error = null
}: NewStrategyModalProps) {
  const [name, setName] = useState("");
  const [paramsText, setParamsText] = useState("{\n \n}");
  const [note, setNote] = useState("");
  const { tr } = useLanguage();

  if (!open) return null;

  const handleSubmit = () => {
    let params: Record<string, any> = {};
    try {
      params = paramsText.trim() ? JSON.parse(paramsText) : {};
    } catch {
      alert(tr("Params must be valid JSON.", "파라미터는 올바른 JSON이어야 합니다."));
      return;
    }
    if (!name.trim()) {
      alert(tr("Name is required.", "이름을 입력해주세요."));
      return;
    }
    onSubmit({ name: name.trim(), params, note: note.trim() || undefined });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/70 p-6" onClick={onClose}>
      <div
        className="w-full max-w-2xl rounded-xl border border-gray-800 bg-[#0d1117] shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-gray-800 px-6 py-4">
          <h2 className="text-lg font-semibold">{tr("New Strategy", "새 전략")}</h2>
          <button className="text-sm text-gray-400 hover:text-gray-200" onClick={onClose}>
            {tr("Close", "닫기")}
          </button>
        </div>

        <div className="px-6 py-5 space-y-4 text-sm">
          {error && <div className="text-red-400">{error}</div>}

          <div>
            <label className="text-xs text-gray-400 mb-2 block">{tr("Name", "이름")}</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2"
              placeholder={tr("My Custom Strategy", "내 커스텀 전략")}
            />
          </div>

          <div>
            <label className="text-xs text-gray-400 mb-2 block">{tr("Params (JSON)", "파라미터 (JSON)")}</label>
            <textarea
              value={paramsText}
              onChange={(e) => setParamsText(e.target.value)}
              className="w-full h-40 bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 font-mono text-xs"
            />
          </div>

          <div>
            <label className="text-xs text-gray-400 mb-2 block">{tr("Note (optional)", "메모 (선택)")}</label>
            <input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2"
              placeholder={tr("Memo...", "메모...")}
            />
          </div>
        </div>

        <div className="flex gap-3 border-t border-gray-800 px-6 py-4">
          <button
            onClick={onClose}
            className="flex-1 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm font-medium"
            type="button"
          >
            {tr("Cancel", "취소")}
          </button>
          <button
            onClick={handleSubmit}
            className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium disabled:opacity-60"
            type="button"
            disabled={loading}
          >
            {loading ? tr("Saving...", "저장 중...") : tr("Save", "저장")}
          </button>
        </div>
      </div>
    </div>
  );
}
