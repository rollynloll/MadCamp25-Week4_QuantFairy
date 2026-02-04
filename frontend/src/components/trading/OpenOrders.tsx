import { useLanguage } from "@/contexts/LanguageContext";
import type { UiOrder } from "@/utils/tradingOrderUtils";

type Props = {
  orders: UiOrder[];
  filledOrders?: UiOrder[];
  view?: "open" | "filled";
  onViewChange?: (v: "open" | "filled") => void;
};

export default function OpenOrders({ orders, filledOrders = [], view, onViewChange }: Props) {
  const { tr } = useLanguage();
  const activeOrders = view === "open" ? orders : filledOrders;
  const isOpen = view === "open";

  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">{tr("Orders", "주문 내역")}</h2>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => onViewChange?.("open")}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              isOpen
                ? "bg-blue-600/20 text-blue-400"
                : "bg-gray-800 hover:bg-gray-700 text-gray-300"
            }`}
          >
            {tr("Open", "미체결")}
          </button>
          <button
            type="button"
            onClick={() => onViewChange?.("filled")}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              !isOpen
                ? "bg-blue-600/20 text-blue-400"
                : "bg-gray-800 hover:bg-gray-700 text-gray-300"
            }`}
          >
            {tr("Filled", "체결")}
          </button>
        </div>
      </div>

      <div className="space-y-1 max-h-[360px] overflow-y-auto pr-1">
        <div className="grid grid-cols-9 gap-4 px-3 py-2 text-xs text-gray-500 font-medium border-b border-gray-800 sticky top-0 bg-[#0d1117] z-10">
          <div>{tr("Order ID", "주문 번호")}</div>
          <div>{tr("Symbol", "종목")}</div>
          <div>{tr("Side", "구분")}</div>
          <div>{tr("Type", "종류")}</div>
          <div className="text-right">{tr("Qty", "수량")}</div>
          <div className="text-right">{tr("Filled", "체결량")}</div>
          <div className="text-right">{tr("Price", "기격")}</div>
          <div>{tr("Status", "상태")}</div>
          <div>{tr("Strategy", "전략")}</div>
        </div>

        {activeOrders.map((order) => (
          <div
            key={order.id}
            className="grid grid-cols-9 gap-4 px-3 py-3 hover:bg-gray-800/50 rounded transition-colors text-sm"
          >
            <div className="font-mono text-gray-400">{order.id}</div>
            <div className="font-semibold">{order.symbol}</div>
            <div
              className={`font-semibold ${
                order.side === "BUY" ? "text-green-500" : "text-red-500"
              }`}
            >
              {order.side}
            </div>
            <div className="text-gray-400">{order.type}</div>
            <div className="text-right font-mono">{order.qty}</div>
            <div className="text-right font-mono text-gray-400">
              {order.filled}
            </div>
            <div className="text-right font-mono">
              {typeof order.price === "number" ? `$${order.price.toFixed(2)}` : "-"}
            </div>
            <div>
              <span
                className={`px-2 py-0.5 rounded text-xs ${
                  order.status === "PENDING"
                    ? "bg-yellow-600/20 text-yellow-400"
                    : order.status === "PARTIAL"
                    ? "bg-blue-600/20 text-blue-400"
                    : "bg-green-600/20 text-green-400"
                }`}
              >
                {order.status}
              </span>
            </div>
            <div className="text-xs text-gray-500">{order.strategy}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
