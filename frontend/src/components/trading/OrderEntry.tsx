import { useLanguage } from "@/contexts/LanguageContext";

export default function OrderEntry() {
  const { tr } = useLanguage();
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">{tr("New Order", "신규 주문")}</h2>
      <div className="space-y-4">
        <div>
          <label className="text-sm text-gray-400 mb-2 block">{tr("Symbol", "종목")}</label>
          <input
            type="text"
            placeholder="AAPL"
            className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm font-mono uppercase"
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <button className="py-2 bg-green-600/20 hover:bg-green-600/30 text-green-400 rounded text-sm font-medium transition-colors">
            {tr("BUY", "매수")}
          </button>
          <button className="py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded text-sm font-medium transition-colors">
            {tr("SELL", "매도")}
          </button>
        </div>
        <div>
          <label className="text-sm text-gray-400 mb-2 block">{tr("Order Type", "주문 유형")}</label>
          <select className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm">
            <option>{tr("LIMIT", "지정가")}</option>
            <option>{tr("MARKET", "시장가")}</option>
            <option>{tr("STOP", "스탑")}</option>
            <option>{tr("STOP LIMIT", "스탑 리밋")}</option>
          </select>
        </div>
        <div>
          <label className="text-sm text-gray-400 mb-2 block">{tr("Quantity", "수량")}</label>
          <input
            type="number"
            placeholder="100"
            className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm font-mono"
          />
        </div>
        <div>
          <label className="text-sm text-gray-400 mb-2 block">{tr("Price", "가격")}</label>
          <input
            type="number"
            placeholder="178.25"
            step="0.01"
            className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm font-mono"
          />
        </div>
        <button className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition-colors">
          {tr("Place Order", "주문 실행")}
        </button>
      </div>
    </div>
  );
}
