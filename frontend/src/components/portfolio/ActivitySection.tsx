import StatusBadge from "./StatusBadge";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import type { AlertItem, BotRun, Order } from "@/types/portfolio";

type tab = "orders" | "trades" | "alerts" | "runs";

interface ActivityProps {
  tab: tab;
  onTabChange: (tab: tab) => void;
  orders: Order[];
  alerts: AlertItem[];
  botRuns: BotRun[];
}

export default function ActivitySection({
  tab,
  onTabChange,
  orders,
  alerts,
  botRuns
}: ActivityProps) {
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded">
      <div className="flex border-b border-gray-800">
        <button
          onClick={() => onTabChange("orders")}
          className={`px-6 py-3 text-sm font-medium transition-colors ${
            tab === "orders" ? "text-white border-b-2 border-blue-500" : "text-gray-500"
          }`}
        >
          Orders
        </button>
        <button
          onClick={() => onTabChange("trades")}
          className={`px-6 py-3 text-sm font-medium transition-colors ${
            tab === "trades" ? "text-white border-b-2 border-blue-500" : "text-gray-500"
          }`}
        >
          Trades
        </button>
        <button
          onClick={() => onTabChange("alerts")}
          className={`px-6 py-3 text-sm font-medium transition-colors ${
            tab === "alerts" ? "text-white border-b-2 border-blue-500" : "text-gray-500"
          }`}
        >
          Alerts
        </button>
        <button
          onClick={() => onTabChange("runs")}
          className={`px-6 py-3 text-sm font-medium transition-colors ${
            tab === "runs" ? "text-white border-b-2 border-blue-500" : "text-gray-500"
          }`}
        >
          Bot Runs
        </button>
      </div>

      <div className="p-4">
        {tab === "orders" && (
          <div className="space-y-1">
            {orders.map((order) => (
              <div key={order.id} className="flex items-center justify-between py-2 px-3 hover:bg-gray-900/30 rounded text-sm">
                <div className="flex items-center gap-4">
                  <span className="text-xs font-mono text-gray-500 w-16">{order.time}</span>
                  <span className={`font-semibold w-12 ${order.type === "BUY" ? "text-green-500" : "text-red-500"}`}>
                    {order.type}
                  </span>
                  <span className="font-semibold w-16">{order.symbol}</span>
                  <span className="font-mono text-gray-400">{order.qty}</span>
                  <StatusBadge status={order.status} />
                </div>
                <span className="text-xs text-gray-500">{order.strategy}</span>
              </div>
            ))}
          </div>
        )}

        {tab === "alerts" && (
          <div className="space-y-2">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-3 rounded border ${
                  alert.level === "error"
                    ? "bg-red-600/10 border-red-500/30"
                    : "bg-yellow-600/10 border-yellow-500/30"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-2 flex-1">
                    <AlertCircle
                      className={`w-4 h-4 mt-0.5 ${
                        alert.level === "error" ? "text-red-400" : "text-yellow-400"
                      }`}
                    />
                    <div className="flex-1">
                      <div className="text-sm">{alert.message}</div>
                      <div className="text-xs text-gray-500 mt-1">{alert.time}</div>
                    </div>
                  </div>
                  <span className="text-xs text-gray-500">{alert.strategy}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "runs" && (
          <div className="space-y-1">
            {botRuns.map((run) => (
              <div key={run.id} className="flex items-center justify-between py-2 px-3 hover:bg-gray-900/30 rounded text-sm">
                <div className="flex items-center gap-4">
                  <span className="text-xs font-mono text-gray-500 w-16">{run.time}</span>
                  {run.status === "success" ? (
                    <CheckCircle2 className="w-4 h-4 text-green-500" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-red-500" />
                  )}
                  <span className={run.status === "success" ? "text-green-500" : "text-red-500"}>
                    {run.status.toUpperCase()}
                  </span>
                  <span className="text-gray-500 font-mono text-xs">{run.duration}</span>
                  <span className="text-gray-400">{run.trades} trades</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "trades" && (
          <div className="text-sm text-gray-500 text-center py-8">
            No recent trades
          </div>
        )}
      </div>
    </div>
  );
}