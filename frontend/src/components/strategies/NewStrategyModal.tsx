import { useState } from "react";

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

  if (!open) return null;

  const handleSubmit = () => {
    let params: Record<string, any> = {};
    try {
      params = paramsText.trim() ? JSON.parse(paramsText) : {};
    } catch {
      alert("Params must be valid JSON.");
      return;
    }
    if (!name.trim()) {
      alert("Name is required.");
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
          <h2 className="text-lg font-semibold">New Strategy</h2>
          <button className="text-sm text-gray-400 hover:text-gray-200" onClick={onClose}>
            Close
          </button>
        </div>

        <div className="px-6 py-5 space-y-4 text-sm">
          {error && <div className="text-red-400">{error}</div>}

          <div>
            <label className="text-xs text-gray-400 mb-2 block">Name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2"
              placeholder="My Custom Strategy"
            />
          </div>

          <div>
            <label className="text-xs text-gray-400 mb-2 block">Params (JSON)</label>
            <textarea
              value={paramsText}
              onChange={(e) => setParamsText(e.target.value)}
              className="w-full h-40 bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 font-mono text-xs"
            />
          </div>

          <div>
            <label className="text-xs text-gray-400 mb-2 block">Note (optional)</label>
            <input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2"
              placeholder="Memo..."
            />
          </div>
        </div>

        <div className="flex gap-3 border-t border-gray-800 px-6 py-4">
          <button
            onClick={onClose}
            className="flex-1 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm font-medium"
            type="button"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium disabled:opacity-60"
            type="button"
            disabled={loading}
          >
            {loading ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}