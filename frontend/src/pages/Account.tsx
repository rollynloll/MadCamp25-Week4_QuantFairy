import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  User,
  Lock,
  LogOut,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Bell,
} from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { getSupabaseClient } from "@/lib/supabaseClient";

export function Account() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [nickname, setNickname] = useState("John Trader");
  const [tradingMode, setTradingMode] = useState<"paper" | "live">("paper");
  const [showLiveWarning, setShowLiveWarning] = useState(false);
  const [notifications, setNotifications] = useState({
    tradeAlerts: true,
    riskAlerts: true,
    systemAlerts: false,
  });

  const handleLogout = async () => {
    try {
      const supabase = getSupabaseClient();
      await supabase.auth.signOut();
    } finally {
      navigate("/login");
    }
  };

  const handleModeChange = (mode: "paper" | "live") => {
    if (mode === "live") {
      setShowLiveWarning(true);
    } else {
      setTradingMode(mode);
      setShowLiveWarning(false);
    }
  };

  const confirmLiveMode = () => {
    setTradingMode("live");
    setShowLiveWarning(false);
  };

  return (
    <div className="min-h-screen bg-[#0a0d14] p-8">
      {/* Header */}
      <div className="max-w-[1200px] mx-auto mb-8">
        <h1 className="text-3xl font-semibold mb-2">
          {t("account.title")}
        </h1>
        <p className="text-gray-400">{t("account.subtitle")}</p>
      </div>

      {/* Main Content */}
      <div className="max-w-[1200px] mx-auto space-y-8">
        {/* Section 1 - Profile */}
        <div className="bg-[#0d1117] border border-gray-800 rounded-xl p-8">
          <div className="flex items-center gap-3 mb-6">
            <User className="w-5 h-5 text-emerald-400" />
            <h2 className="text-xl font-semibold">
              {t("account.section.profile")}
            </h2>
          </div>

          <div className="space-y-6">
            {/* Email Display */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                {t("form.email")}
              </label>
              <div className="bg-[#0a0d14] border border-gray-800 rounded-xl px-4 py-3 text-sm text-gray-500">
                john.trader@example.com
              </div>
            </div>

            {/* Editable Nickname */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                {t("form.nickname")}
              </label>
              <input
                type="text"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                className="w-full bg-[#0a0d14] border border-gray-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
              />
            </div>

            {/* Actions */}
            <div className="flex gap-4">
              <button className="px-6 py-2.5 bg-gray-800 hover:bg-gray-700 rounded-xl text-sm font-medium transition-all flex items-center gap-2">
                <Lock className="w-4 h-4" />
                {t("account.button.changePassword")}
              </button>
              <button
                onClick={handleLogout}
                className="px-6 py-2.5 bg-red-600/10 hover:bg-red-600/20 text-red-400 rounded-xl text-sm font-medium transition-all flex items-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                {t("account.button.logout")}
              </button>
            </div>
          </div>
        </div>

        {/* Section 2 - Broker Connections */}
        <div className="bg-[#0d1117] border border-gray-800 rounded-xl p-8">
          <h2 className="text-xl font-semibold mb-6">
            {t("account.section.brokers")}
          </h2>

          <div className="grid grid-cols-2 gap-6">
            {/* Paper Trading Card */}
            <div className="bg-[#0a0d14] border border-gray-800 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">{t("account.card.paper")}</h3>
                <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-medium rounded-lg flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {t("account.status.connected")}
                </span>
              </div>

              {/* Account Summary */}
              <div className="mb-6 p-4 bg-[#0d1117] border border-gray-800 rounded-lg">
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">
                      {t("account.label.accountId")}
                    </span>
                    <span className="font-mono">PAPER_001</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">
                      {t("account.label.equity")}
                    </span>
                    <span className="font-mono text-emerald-400">
                      $102,450.00
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">
                      {t("account.label.cash")}
                    </span>
                    <span className="font-mono">$45,230.00</span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <button className="flex-1 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm font-medium transition-all">
                  {t("account.button.reconnect")}
                </button>
                <button className="flex-1 px-4 py-2 bg-red-600/10 hover:bg-red-600/20 text-red-400 rounded-lg text-sm font-medium transition-all">
                  {t("account.button.disconnect")}
                </button>
              </div>
            </div>

            {/* Live Trading Card */}
            <div className="bg-[#0a0d14] border border-gray-800 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">{t("account.card.live")}</h3>
                <span className="px-3 py-1 bg-gray-800 text-gray-400 text-xs font-medium rounded-lg flex items-center gap-1.5">
                  <XCircle className="w-3.5 h-3.5" />
                  {t("account.status.disconnected")}
                </span>
              </div>

              {/* Warning */}
              <div className="mb-6 p-4 bg-yellow-500/5 border border-yellow-500/20 rounded-lg flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-yellow-200/80">
                  {t("account.warning.live")}
                </div>
              </div>

              {/* Connect Button */}
              <button className="w-full px-4 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white rounded-lg text-sm font-medium transition-all shadow-lg shadow-emerald-500/20">
                {t("account.button.connectLive")}
              </button>
            </div>
          </div>
        </div>

        {/* Section 3 - Trading Mode */}
        <div className="bg-[#0d1117] border border-gray-800 rounded-xl p-8">
          <h2 className="text-xl font-semibold mb-6">
            {t("account.section.mode")}
          </h2>

          {/* Segmented Toggle */}
          <div className="inline-flex bg-[#0a0d14] border border-gray-800 rounded-xl p-1">
            <button
              onClick={() => handleModeChange("paper")}
              className={`px-8 py-2.5 rounded-lg text-sm font-medium transition-all ${
                tradingMode === "paper"
                  ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/20"
                  : "text-gray-400 hover:text-gray-300"
              }`}
            >
              {t("account.mode.paper")}
            </button>
            <button
              onClick={() => handleModeChange("live")}
              className={`px-8 py-2.5 rounded-lg text-sm font-medium transition-all ${
                tradingMode === "live"
                  ? "bg-red-500 text-white shadow-lg shadow-red-500/20"
                  : "text-gray-400 hover:text-gray-300"
              }`}
            >
              {t("account.mode.live")}
            </button>
          </div>

          <p className="mt-4 text-sm text-gray-500">
            {t("account.mode.current")} {" "}
            <span
              className={
                tradingMode === "paper" ? "text-emerald-400" : "text-red-400"
              }
            >
              {tradingMode === "paper"
                ? t("account.mode.paperLabel")
                : t("account.mode.liveLabel")}
            </span>
          </p>
        </div>

        {/* Section 4 - Notifications */}
        <div className="bg-[#0d1117] border border-gray-800 rounded-xl p-8">
          <div className="flex items-center gap-3 mb-6">
            <Bell className="w-5 h-5 text-emerald-400" />
            <h2 className="text-xl font-semibold">
              {t("account.section.notifications")}
            </h2>
          </div>

          <div className="space-y-4">
            {/* Trade Alerts */}
            <div className="flex items-center justify-between p-4 bg-[#0a0d14] border border-gray-800 rounded-xl">
              <div>
                <div className="font-medium mb-1">
                  {t("account.notification.tradeAlerts.title")}
                </div>
                <div className="text-sm text-gray-500">
                  {t("account.notification.tradeAlerts.desc")}
                </div>
              </div>
              <button
                onClick={() =>
                  setNotifications({
                    ...notifications,
                    tradeAlerts: !notifications.tradeAlerts,
                  })
                }
                className={`relative w-12 h-6 rounded-full transition-all ${
                  notifications.tradeAlerts ? "bg-emerald-500" : "bg-gray-700"
                }`}
              >
                <div
                  className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                    notifications.tradeAlerts ? "translate-x-6" : ""
                  }`}
                ></div>
              </button>
            </div>

            {/* Risk Alerts */}
            <div className="flex items-center justify-between p-4 bg-[#0a0d14] border border-gray-800 rounded-xl">
              <div>
                <div className="font-medium mb-1">
                  {t("account.notification.riskAlerts.title")}
                </div>
                <div className="text-sm text-gray-500">
                  {t("account.notification.riskAlerts.desc")}
                </div>
              </div>
              <button
                onClick={() =>
                  setNotifications({
                    ...notifications,
                    riskAlerts: !notifications.riskAlerts,
                  })
                }
                className={`relative w-12 h-6 rounded-full transition-all ${
                  notifications.riskAlerts ? "bg-emerald-500" : "bg-gray-700"
                }`}
              >
                <div
                  className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                    notifications.riskAlerts ? "translate-x-6" : ""
                  }`}
                ></div>
              </button>
            </div>

            {/* System Alerts */}
            <div className="flex items-center justify-between p-4 bg-[#0a0d14] border border-gray-800 rounded-xl">
              <div>
                <div className="font-medium mb-1">
                  {t("account.notification.systemAlerts.title")}
                </div>
                <div className="text-sm text-gray-500">
                  {t("account.notification.systemAlerts.desc")}
                </div>
              </div>
              <button
                onClick={() =>
                  setNotifications({
                    ...notifications,
                    systemAlerts: !notifications.systemAlerts,
                  })
                }
                className={`relative w-12 h-6 rounded-full transition-all ${
                  notifications.systemAlerts ? "bg-emerald-500" : "bg-gray-700"
                }`}
              >
                <div
                  className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                    notifications.systemAlerts ? "translate-x-6" : ""
                  }`}
                ></div>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Live Mode Warning Modal */}
      {showLiveWarning && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-8 z-50">
          <div className="bg-[#0d1117] border border-red-500/50 rounded-xl p-8 max-w-md shadow-2xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-400" />
              </div>
              <h3 className="text-xl font-semibold">
                {t("account.modal.title")}
              </h3>
            </div>

            <p className="text-gray-400 mb-6">{t("account.modal.body")}</p>

            <div className="flex gap-3">
              <button
                onClick={() => setShowLiveWarning(false)}
                className="flex-1 px-4 py-2.5 bg-gray-800 hover:bg-gray-700 rounded-xl text-sm font-medium transition-all"
              >
                {t("account.modal.cancel")}
              </button>
              <button
                onClick={confirmLiveMode}
                className="flex-1 px-4 py-2.5 bg-red-600 hover:bg-red-700 rounded-xl text-sm font-medium transition-all"
              >
                {t("account.modal.confirm")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Account;
