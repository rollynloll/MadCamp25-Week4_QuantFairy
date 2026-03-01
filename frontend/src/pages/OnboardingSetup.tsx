import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Shield, TrendingUp, Zap } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

type RiskLevel = "conservative" | "balanced" | "aggressive" | null;

export function OnboardingSetup() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [selectedRisk, setSelectedRisk] = useState<RiskLevel>(null);

  const riskLabel = selectedRisk
    ? t(`onboarding.setup.risk.${selectedRisk}`)
    : "";
  const recommendedTitle = selectedRisk
    ? t("onboarding.setup.recommendedTitle").replace("{risk}", riskLabel)
    : "";

  const handleComplete = () => {
    if (selectedRisk) {
      navigate("/");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0d14] via-[#0d1117] to-[#0a0d14] flex items-center justify-center p-8">
      <div className="w-full max-w-[720px]">
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
              <span className="text-sm text-gray-500">Welcome</span>
            </div>
            <div className="w-12 h-px bg-gray-800"></div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center text-sm text-emerald-400">
                ✓
              </div>
              <span className="text-sm text-gray-500">Connect</span>
            </div>
            <div className="w-12 h-px bg-gray-800"></div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center text-sm font-semibold">
                3
              </div>
              <span className="text-sm text-emerald-400 font-medium">
                Setup
              </span>
            </div>
          </div>

          {/* Setup Content */}
          <div className="text-center mb-12">
            <h2 className="text-3xl font-semibold mb-4">
              {t("onboarding.setup.title")}
            </h2>
            <p className="text-gray-400 text-lg">
              {t("onboarding.setup.subtitle")}
            </p>
          </div>

          {/* Risk Selection Cards */}
          <div className="grid grid-cols-3 gap-6 mb-12">
            {/* Conservative */}
            <button
              onClick={() => setSelectedRisk("conservative")}
              className={`bg-[#0a0d14] border rounded-xl p-6 text-center transition-all ${
                selectedRisk === "conservative"
                  ? "border-emerald-500 ring-2 ring-emerald-500/20"
                  : "border-gray-800 hover:border-gray-700"
              }`}
            >
              <div
                className={`w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4 ${
                  selectedRisk === "conservative"
                    ? "bg-emerald-500/10"
                    : "bg-gray-800"
                }`}
              >
                <Shield
                  className={`w-6 h-6 ${
                    selectedRisk === "conservative"
                      ? "text-emerald-400"
                      : "text-gray-400"
                  }`}
                />
              </div>
              <h3 className="font-semibold mb-2">
                {t("onboarding.setup.risk.conservative")}
              </h3>
              <p className="text-sm text-gray-400">
                {t("onboarding.setup.risk.conservativeDesc")}
              </p>
              <div className="mt-4 text-xs text-gray-500">
                {t("onboarding.setup.risk.conservativeTarget")}
              </div>
            </button>

            {/* Balanced */}
            <button
              onClick={() => setSelectedRisk("balanced")}
              className={`bg-[#0a0d14] border rounded-xl p-6 text-center transition-all ${
                selectedRisk === "balanced"
                  ? "border-emerald-500 ring-2 ring-emerald-500/20"
                  : "border-gray-800 hover:border-gray-700"
              }`}
            >
              <div
                className={`w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4 ${
                  selectedRisk === "balanced"
                    ? "bg-emerald-500/10"
                    : "bg-gray-800"
                }`}
              >
                <TrendingUp
                  className={`w-6 h-6 ${
                    selectedRisk === "balanced"
                      ? "text-emerald-400"
                      : "text-gray-400"
                  }`}
                />
              </div>
              <h3 className="font-semibold mb-2">
                {t("onboarding.setup.risk.balanced")}
              </h3>
              <p className="text-sm text-gray-400">
                {t("onboarding.setup.risk.balancedDesc")}
              </p>
              <div className="mt-4 text-xs text-gray-500">
                {t("onboarding.setup.risk.balancedTarget")}
              </div>
            </button>

            {/* Aggressive */}
            <button
              onClick={() => setSelectedRisk("aggressive")}
              className={`bg-[#0a0d14] border rounded-xl p-6 text-center transition-all ${
                selectedRisk === "aggressive"
                  ? "border-emerald-500 ring-2 ring-emerald-500/20"
                  : "border-gray-800 hover:border-gray-700"
              }`}
            >
              <div
                className={`w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4 ${
                  selectedRisk === "aggressive"
                    ? "bg-emerald-500/10"
                    : "bg-gray-800"
                }`}
              >
                <Zap
                  className={`w-6 h-6 ${
                    selectedRisk === "aggressive"
                      ? "text-emerald-400"
                      : "text-gray-400"
                  }`}
                />
              </div>
              <h3 className="font-semibold mb-2">
                {t("onboarding.setup.risk.aggressive")}
              </h3>
              <p className="text-sm text-gray-400">
                {t("onboarding.setup.risk.aggressiveDesc")}
              </p>
              <div className="mt-4 text-xs text-gray-500">
                {t("onboarding.setup.risk.aggressiveTarget")}
              </div>
            </button>
          </div>

          {/* Recommended Strategies Preview */}
          {selectedRisk && (
            <div className="mb-8 p-6 bg-[#0a0d14] border border-gray-800 rounded-xl">
              <h3 className="text-sm font-semibold text-gray-300 mb-4">
                {recommendedTitle}
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-[#0d1117] border border-gray-800 rounded-lg">
                  <div>
                    <div className="font-medium text-sm">
                      {t("onboarding.setup.strategy.meanReversion")}
                    </div>
                    <div className="text-xs text-gray-500">
                      {t("onboarding.setup.strategy.meanReversionDesc")}
                    </div>
                  </div>
                  <div className="text-xs text-emerald-400">+12.3% YTD</div>
                </div>
                <div className="flex items-center justify-between p-3 bg-[#0d1117] border border-gray-800 rounded-lg">
                  <div>
                    <div className="font-medium text-sm">
                      {t("onboarding.setup.strategy.momentum")}
                    </div>
                    <div className="text-xs text-gray-500">
                      {t("onboarding.setup.strategy.momentumDesc")}
                    </div>
                  </div>
                  <div className="text-xs text-emerald-400">+18.7% YTD</div>
                </div>
                <div className="flex items-center justify-between p-3 bg-[#0d1117] border border-gray-800 rounded-lg">
                  <div>
                    <div className="font-medium text-sm">
                      {t("onboarding.setup.strategy.pairs")}
                    </div>
                    <div className="text-xs text-gray-500">
                      {t("onboarding.setup.strategy.pairsDesc")}
                    </div>
                  </div>
                  <div className="text-xs text-emerald-400">+9.4% YTD</div>
                </div>
              </div>
            </div>
          )}

          {/* Complete Button */}
          <button
            onClick={handleComplete}
            disabled={!selectedRisk}
            className={`w-full font-medium py-3 rounded-xl transition-all ${
              selectedRisk
                ? "bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white shadow-lg shadow-emerald-500/20"
                : "bg-gray-800 text-gray-500 cursor-not-allowed"
            }`}
          >
            {t("onboarding.setup.button.complete")}
          </button>
        </div>
      </div>
    </div>
  );
}

export default OnboardingSetup;
