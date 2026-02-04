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
  const gridCols =
    "grid-cols-[minmax(140px,1.3fr)_80px_84px_92px_82px_92px_86px_110px_minmax(120px,1fr)]";

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

      <div className="max-h-[360px] overflow-auto pr-1">
        <div className={`sticky top-0 z-10 hidden ${gridCols} gap-4 border-b border-gray-800 bg-[#0d1117] px-3 py-2 text-xs font-medium text-gray-500 md:grid`}>
          <div className="truncate">{tr("Order ID", "주문 번호")}</div>
          <div className="truncate">{tr("Symbol", "종목")}</div>
          <div className="truncate">{tr("Side", "구분")}</div>
          <div className="truncate">{tr("Type", "종류")}</div>
          <div className="truncate text-right">{tr("Qty", "수량")}</div>
          <div className="truncate text-right">{tr("Filled", "체결량")}</div>
          <div className="truncate text-right">{tr("Price", "가격")}</div>
          <div className="truncate">{tr("Status", "상태")}</div>
          <div className="truncate">{tr("Strategy", "전략")}</div>
        </div>

        <div className="space-y-1">
          {activeOrders.map((order) => (
          <div
            key={order.id}
            className="rounded px-3 py-3 text-sm transition-colors hover:bg-gray-800/50"
          >
            <div className={`flex flex-col gap-2 md:grid ${gridCols} md:items-center md:gap-4`}>
              <div className="min-w-0 font-mono text-gray-400 md:truncate">{order.id}</div>
              <div className="min-w-0 font-semibold md:truncate">{order.symbol}</div>
              <div
                className={`font-semibold ${
                  order.side === "BUY" ? "text-green-500" : "text-red-500"
                }`}
              >
                {order.side}
              </div>
              <div className="min-w-0 truncate text-gray-400">{order.type}</div>
              <div className="font-mono md:text-right">{order.qty}</div>
              <div className="font-mono text-gray-400 md:text-right">
                {order.filled}
              </div>
              <div className="font-mono md:text-right">
                {typeof order.price === "number" ? `$${order.price.toFixed(2)}` : "-"}
              </div>
              <div className="min-w-0">
                <span
                  className={`inline-block rounded px-2 py-0.5 text-xs ${
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
              <div className="min-w-0 truncate text-xs text-gray-500">{order.strategy}</div>
            </div>
          </div>
          ))}
        </div>
      </div>
    </div>
  );
}
