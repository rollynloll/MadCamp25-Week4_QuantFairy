import StatusBadge from "./StatusBadge";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import type { AlertItem, BotRun, Order } from "@/types/portfolio";
import { useLanguage } from "@/contexts/LanguageContext";

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
  const { tr } = useLanguage();
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded">
      <div className="flex border-b border-gray-800">
        <button
          onClick={() => onTabChange("orders")}
          className={`px-6 py-3 text-sm font-medium transition-colors ${
            tab === "orders" ? "text-white border-b-2 border-blue-500" : "text-gray-500"
          }`}
        >
          {tr("Orders", "주문")}
        </button>
        <button
          onClick={() => onTabChange("trades")}
          className={`px-6 py-3 text-sm font-medium transition-colors ${
            tab === "trades" ? "text-white border-b-2 border-blue-500" : "text-gray-500"
          }`}
        >
          {tr("Trades", "체결 내역")}
        </button>
        <button
          onClick={() => onTabChange("alerts")}
          className={`px-6 py-3 text-sm font-medium transition-colors ${
            tab === "alerts" ? "text-white border-b-2 border-blue-500" : "text-gray-500"
          }`}
        >
          {tr("Alerts", "알림")}
        </button>
        <button
          onClick={() => onTabChange("runs")}
          className={`px-6 py-3 text-sm font-medium transition-colors ${
            tab === "runs" ? "text-white border-b-2 border-blue-500" : "text-gray-500"
          }`}
        >
          {tr("Bot Runs", "봇 실행 기록")}
        </button>
      </div>

      <div className="p-4">
        {tab === "orders" && (
          <div className="space-y-1">
            <div className="hidden sm:grid sm:grid-cols-[160px_56px_72px_minmax(100px,1fr)_96px_minmax(120px,1fr)] sm:items-center sm:gap-4 px-3 pt-1 pb-2 text-[11px] uppercase tracking-wide text-gray-500">
              <span>{tr("Time", "시간")}</span>
              <span>{tr("Side", "구분")}</span>
              <span>{tr("Symbol", "종목")}</span>
              <span className="sm:text-right">{tr("Qty", "수량")}</span>
              <span>{tr("Status", "상태")}</span>
              <span className="sm:text-right">{tr("Strategy", "전략")}</span>
            </div>
            {orders.map((order) => (
              <div
                key={order.id}
                className="py-2 px-3 hover:bg-gray-900/30 rounded text-sm"
              >
                <div className="flex flex-col gap-2 sm:grid sm:grid-cols-[160px_56px_72px_minmax(100px,1fr)_96px_minmax(120px,1fr)] sm:items-center sm:gap-4">
                  <span className="text-xs font-mono text-gray-500 truncate whitespace-nowrap">
                    {order.time}
                  </span>
                  <span className={`font-semibold ${order.type === "BUY" ? "text-green-500" : "text-red-500"}`}>
                    {order.type}
                  </span>
                  <span className="font-semibold truncate">{order.symbol}</span>
                  <span className="font-mono text-gray-400 sm:text-right">{order.qty}</span>
                  <StatusBadge status={order.status} />
                  <span className="text-xs text-gray-500 truncate sm:text-right">{order.strategy}</span>
                </div>
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
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex items-start gap-2 flex-1 min-w-0">
                    <AlertCircle
                      className={`w-4 h-4 mt-0.5 ${
                        alert.level === "error" ? "text-red-400" : "text-yellow-400"
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm">{alert.message}</div>
                      <div className="text-xs text-gray-500 mt-1">{alert.time}</div>
                    </div>
                  </div>
                  <span className="text-xs text-gray-500 truncate">{alert.strategy}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "runs" && (
          <div className="space-y-1">
            <div className="hidden sm:grid sm:grid-cols-[160px_minmax(140px,1fr)_96px_minmax(120px,1fr)] sm:items-center sm:gap-4 px-3 pt-1 pb-2 text-[11px] uppercase tracking-wide text-gray-500">
              <span>{tr("Time", "시간")}</span>
              <span>{tr("Status", "상태")}</span>
              <span>{tr("Duration", "소요")}</span>
              <span>{tr("Trades", "거래 수")}</span>
            </div>
            {botRuns.map((run) => (
              <div
                key={run.id}
                className="py-2 px-3 hover:bg-gray-900/30 rounded text-sm"
              >
                <div className="flex flex-col gap-2 sm:grid sm:grid-cols-[160px_minmax(140px,1fr)_96px_minmax(120px,1fr)] sm:items-center sm:gap-4">
                  <span className="text-xs font-mono text-gray-500 truncate whitespace-nowrap">
                    {run.time}
                  </span>
                  <span className="flex items-center gap-2">
                    {run.status === "success" ? (
                      <CheckCircle2 className="w-4 h-4 text-green-500" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-red-500" />
                    )}
                    <span className={run.status === "success" ? "text-green-500" : "text-red-500"}>
                      {run.status.toUpperCase()}
                    </span>
                  </span>
                  <span className="text-gray-500 font-mono text-xs sm:text-right">{run.duration}</span>
                  <span className="text-gray-400 sm:text-right">
                    {run.trades} {tr("trades", "거래 내역")}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "trades" && (
          <div className="space-y-2">
            <div className="hidden sm:grid sm:grid-cols-[160px_56px_72px_minmax(100px,1fr)_96px_minmax(120px,1fr)] sm:items-center sm:gap-4 px-3 pt-1 pb-2 text-[11px] uppercase tracking-wide text-gray-500">
              <span>{tr("Time", "시간")}</span>
              <span>{tr("Side", "구분")}</span>
              <span>{tr("Symbol", "종목")}</span>
              <span className="sm:text-right">{tr("Qty", "수량")}</span>
              <span>{tr("Status", "상태")}</span>
              <span className="sm:text-right">{tr("Strategy", "전략")}</span>
            </div>
            <div className="text-sm text-gray-500 text-center py-8">
              {tr("No recent trades", "최근 체결이 없습니다")}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
