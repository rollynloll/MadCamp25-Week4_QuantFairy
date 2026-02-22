import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle2, Loader2, AlertCircle, HelpCircle } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

type ConnectionStatus = "not_connected" | "connecting" | "connected" | "failed";

export function OnboardingConnect() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [status, setStatus] = useState<ConnectionStatus>("not_connected");

  const handleConnect = () => {
    setStatus("connecting");

    // Simulate connection process
    setTimeout(() => {
      setStatus("connected");
    }, 2000);
  };

  const handleContinue = () => {
    if (status === "connected") {
      navigate("/onboarding/setup");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0d14] via-[#0d1117] to-[#0a0d14] flex items-center justify-center p-8">
      <div className="w-full max-w-[640px]">
        {/* Logo */}
        <div className="mb-12 text-center">
          <h1 className="text-3xl font-bold mb-2 bg-gradient-to-r from-emerald-400 to-teal-500 bg-clip-text text-transparent">
            QuantFairy
          </h1>
        </div>

        {/* Main Card */}
        <div className="bg-[#0d1117] border border-gray-800 rounded-xl p-12 shadow-2xl">
          {/* Step Indicator */}
          <div className="flex items-center justify-center gap-2 mb-12">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center text-sm text-emerald-400">
                ✓
              </div>
              <span className="text-sm text-gray-500">
                {t("onboarding.step.welcome")}
              </span>
            </div>
            <div className="w-12 h-px bg-gray-800"></div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center text-sm font-semibold">
                2
              </div>
              <span className="text-sm text-emerald-400 font-medium">
                {t("onboarding.step.connect")}
              </span>
            </div>
            <div className="w-12 h-px bg-gray-800"></div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center text-sm text-gray-500">
                3
              </div>
              <span className="text-sm text-gray-500">
                {t("onboarding.step.setup")}
              </span>
            </div>
          </div>

          {/* Connection Card */}
          <div className="mb-8">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-semibold mb-4">
                {t("onboarding.connect.title")}
              </h2>
              <p className="text-gray-400 text-lg">
                {t("onboarding.connect.subtitle")}
              </p>
            </div>

            {/* Status Section */}
            <div className="bg-[#0a0d14] border border-gray-800 rounded-xl p-8 mb-6">
              <div className="flex items-center justify-center mb-6">
                {status === "not_connected" && (
                  <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center">
                    <div className="w-8 h-8 border-2 border-gray-600 rounded-full"></div>
                  </div>
                )}
                {status === "connecting" && (
                  <div className="w-16 h-16 rounded-full bg-emerald-500/10 flex items-center justify-center">
                    <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
                  </div>
                )}
                {status === "connected" && (
                  <div className="w-16 h-16 rounded-full bg-emerald-500/10 flex items-center justify-center">
                    <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                  </div>
                )}
                {status === "failed" && (
                  <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center">
                    <AlertCircle className="w-8 h-8 text-red-400" />
                  </div>
                )}
              </div>

              <div className="text-center mb-6">
                {status === "not_connected" && (
                  <p className="text-gray-400">
                    {t("onboarding.connect.status.notConnected")}
                  </p>
                )}
                {status === "connecting" && (
                  <p className="text-emerald-400">
                    {t("onboarding.connect.status.connecting")}
                  </p>
                )}
                {status === "connected" && (
                  <>
                    <p className="text-emerald-400 font-semibold mb-2">
                      {t("onboarding.connect.status.connectedTitle")}
                    </p>
                    <div className="text-sm text-gray-500">
                      <p>
                        {t("onboarding.connect.status.paperAccount")}: PAPER_ACCOUNT_001
                      </p>
                      <p>
                        {t("onboarding.connect.status.equity")}: $100,000.00
                      </p>
                    </div>
                  </>
                )}
                {status === "failed" && (
                  <>
                    <p className="text-red-400 font-semibold mb-2">
                      {t("onboarding.connect.status.failedTitle")}
                    </p>
                    <p className="text-sm text-gray-500">
                      {t("onboarding.connect.status.failedDesc")}
                    </p>
                  </>
                )}
              </div>

              {status === "not_connected" && (
                <button
                  onClick={handleConnect}
                  className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-medium py-3 rounded-xl transition-all shadow-lg shadow-emerald-500/20"
                >
                  {t("onboarding.connect.button.connect")}
                </button>
              )}

              {status === "failed" && (
                <button
                  onClick={handleConnect}
                  className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-medium py-3 rounded-xl transition-all shadow-lg shadow-emerald-500/20"
                >
                  {t("onboarding.connect.button.retry")}
                </button>
              )}
            </div>

            {/* Secondary Link */}
            <div className="text-center mb-6">
              <a
                href="https://alpaca.markets"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-emerald-400 hover:text-emerald-300 transition-colors"
              >
                {t("onboarding.connect.link.create")}
              </a>
            </div>

            {/* Tooltip */}
            <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
              <HelpCircle className="w-4 h-4" />
              <button className="hover:text-gray-300 transition-colors">
                {t("onboarding.connect.help")}
              </button>
            </div>
          </div>

          {/* Continue Button */}
          <button
            onClick={handleContinue}
            disabled={status !== "connected"}
            className={`w-full font-medium py-3 rounded-xl transition-all ${
              status === "connected"
                ? "bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white shadow-lg shadow-emerald-500/20"
                : "bg-gray-800 text-gray-500 cursor-not-allowed"
            }`}
          >
            {t("onboarding.connect.button.continue")}
          </button>
        </div>
      </div>
    </div>
  );
}

export default OnboardingConnect;
