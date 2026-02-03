import type { OpenOrder } from "@/types/trading";
import { useLanguage } from "@/contexts/LanguageContext";

export default function OpenOrders({ orders }: { orders: OpenOrder[] }) {
  const { tr } = useLanguage();
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">{tr("Open Orders", "미체결 주문")}</h2>
      <div className="space-y-1">
        <div className="grid grid-cols-9 gap-4 px-3 py-2 text-xs text-gray-500 font-medium border-b border-gray-800">
          <div>{tr("Order ID", "주문 ID")}</div>
          <div>{tr("Symbol", "종목")}</div>
          <div>{tr("Side", "방향")}</div>
          <div>{tr("Type", "유형")}</div>
          <div className="text-right">{tr("Qty", "수량")}</div>
          <div className="text-right">{tr("Filled", "체결")}</div>
          <div className="text-right">{tr("Price", "가격")}</div>
          <div>{tr("Status", "상태")}</div>
          <div>{tr("Strategy", "전략")}</div>
        </div>

        {orders.map((order) => (
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
              ${order.price.toFixed(2)}
            </div>
            <div>
              <span
                className={`px-2 py-0.5 rounded text-xs ${
                  order.status === "PENDING"
                    ? "bg-yellow-600/20 text-yellow-400"
                    : "bg-blue-600/20 text-blue-400"
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
