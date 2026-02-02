// src/features/portfolio/components/StrategyEditDrawer.tsx
import type { Strategy } from "@/types/portfolio";
import { X } from "lucide-react";


export function StrategyEditDrawer({
  open,
  strategyId,
  strategies,
  onClose,
  onSave,
}: {
  open: boolean;
  strategyId: number | null;
  strategies: Strategy[];
  onClose: () => void;
  onSave: (strategyId: number) => void;
}) {
  if (!open || strategyId == null) return null;

  const strategy = strategies.find((s) => s.id === strategyId);

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex justify-end">
      <div className="w-[500px] bg-[#0a0d14] border-l border-gray-800 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
          <h3 className="font-semibold">Edit Strategy: {strategy?.name ?? "Unknown"}</h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-800 rounded transition-colors" type="button">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4 space-y-6">
          <div>
            <h4 className="text-sm font-semibold mb-3 text-gray-400">Summary</h4>
            <div className="space-y-2 text-sm">
              <Row label="Current Weight" value="28.5%" />
              <Row label="Target Weight" value="30.0%" />
              <Row label="Positions" value="2" />
              <Row label="P&L (Today)" value="+$445.00" valueClassName="text-green-500" />
            </div>
          </div>

          {/* Parameters */}
          <div>
            <h4 className="text-sm font-semibold mb-3 text-gray-400">Parameters</h4>

            <div className="space-y-4">
              <Field label="Lookback Period">
                <input
                  type="number"
                  defaultValue="20"
                  className="w-full bg-[#0d1117] border border-gray-800 rounded px-3 py-2 text-sm"
                />
              </Field>

              <Field label="Entry Threshold">
                <input
                  type="number"
                  defaultValue="2.0"
                  step="0.1"
                  className="w-full bg-[#0d1117] border border-gray-800 rounded px-3 py-2 text-sm"
                />
              </Field>

              <Field label="Exit Threshold">
                <input
                  type="number"
                  defaultValue="0.5"
                  step="0.1"
                  className="w-full bg-[#0d1117] border border-gray-800 rounded px-3 py-2 text-sm"
                />
              </Field>
            </div>
          </div>

          {/* Risk Limits */}
          <div>
            <h4 className="text-sm font-semibold mb-3 text-gray-400">Risk Limits</h4>

            <div className="space-y-4">
              <Field label="Max Position Size">
                <input
                  type="number"
                  defaultValue="10000"
                  className="w-full bg-[#0d1117] border border-gray-800 rounded px-3 py-2 text-sm"
                />
              </Field>

              <Field label="Stop Loss %">
                <input
                  type="number"
                  defaultValue="5.0"
                  step="0.5"
                  className="w-full bg-[#0d1117] border border-gray-800 rounded px-3 py-2 text-sm"
                />
              </Field>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-800 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm font-medium transition-colors"
            type="button"
          >
            Cancel
          </button>
          <button
            onClick={() => onSave(strategyId)}
            className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition-colors"
            type="button"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}

function Row({
  label,
  value,
  valueClassName,
}: {
  label: string;
  value: string;
  valueClassName?: string;
}) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-500">{label}</span>
      <span className={`font-mono ${valueClassName ?? ""}`}>{value}</span>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="text-sm mb-2 block">{label}</label>
      {children}
    </div>
  );
}
