import { useMemo } from "react";
import { useLanguage } from "@/contexts/LanguageContext";
import type { BarPoint } from "@/hooks/useMarketStream";

interface PriceChartProps {
  symbol: string;
  bars: BarPoint[];
  lastPrice: number;
  status: string;
}

export default function PriceChart({ symbol, bars, lastPrice, status }: PriceChartProps) {
  const { tr } = useLanguage();

  const { path, min, max } = useMemo(() => {
    if (bars.length < 2) {
      return { path: "", min: 0, max: 0 };
    }
    const closes = bars.map((b) => b.close);
    const minVal = Math.min(...closes);
    const maxVal = Math.max(...closes);
    const width = 600;
    const height = 200;
    const pad = 12;
    const scaleX = (idx: number) =>
      pad + (idx / (closes.length - 1)) * (width - pad * 2);
    const scaleY = (value: number) => {
      if (maxVal === minVal) return height / 2;
      return height - pad - ((value - minVal) / (maxVal - minVal)) * (height - pad * 2);
    };
    const d = closes
      .map((value, idx) => `${idx === 0 ? "M" : "L"} ${scaleX(idx)} ${scaleY(value)}`)
      .join(" ");
    return { path: d, min: minVal, max: maxVal };
  }, [bars]);

  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold">{tr("Price", "가격")}</h2>
          <div className="text-xs text-gray-500">
            {symbol} · {tr("Stream", "스트림")}: {status}
          </div>
        </div>
        <div className="text-right">
          <div className="text-lg font-mono font-semibold">{lastPrice ? lastPrice.toFixed(2) : "-"}</div>
          <div className="text-xs text-gray-500">
            {min && max ? `${min.toFixed(2)} - ${max.toFixed(2)}` : ""}
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-gray-800 bg-gradient-to-br from-gray-900/40 to-transparent p-3">
        {path ? (
          <svg viewBox="0 0 600 200" className="w-full h-40">
            <path d={path} fill="none" stroke="#3b82f6" strokeWidth="2" />
          </svg>
        ) : (
          <div className="h-40 flex items-center justify-center text-xs text-gray-500">
            {tr("Waiting for bars...", "봉 데이터 대기 중...")}
          </div>
        )}
      </div>
    </div>
  );
}
