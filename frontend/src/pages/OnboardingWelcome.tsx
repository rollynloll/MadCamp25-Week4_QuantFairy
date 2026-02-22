import { useNavigate } from "react-router-dom";
import { LineChart, TrendingUp, Zap } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

export function OnboardingWelcome() {
  const navigate = useNavigate();
  const { t } = useLanguage();

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
              <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center text-sm font-semibold">
                1
              </div>
              <span className="text-sm text-emerald-400 font-medium">
                {t("onboarding.step.welcome")}
              </span>
            </div>
            <div className="w-12 h-px bg-gray-800"></div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center text-sm text-gray-500">
                2
              </div>
              <span className="text-sm text-gray-500">
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

          {/* Welcome Content */}
          <div className="text-center mb-12">
            <h2 className="text-3xl font-semibold mb-4">
              {t("onboarding.welcome.title")}
            </h2>
            <p className="text-gray-400 text-lg">
              {t("onboarding.welcome.subtitle")}
            </p>
          </div>

          {/* Feature Cards */}
          <div className="grid grid-cols-3 gap-6 mb-12">
            {/* Card 1 */}
            <div className="bg-[#0a0d14] border border-gray-800 rounded-xl p-6 text-center hover:border-emerald-500/50 transition-all">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center mx-auto mb-4">
                <LineChart className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="font-semibold mb-2">
                {t("onboarding.welcome.card.choose.title")}
              </h3>
              <p className="text-sm text-gray-400">
                {t("onboarding.welcome.card.choose.desc")}
              </p>
            </div>

            {/* Card 2 */}
            <div className="bg-[#0a0d14] border border-gray-800 rounded-xl p-6 text-center hover:border-emerald-500/50 transition-all">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="font-semibold mb-2">
                {t("onboarding.welcome.card.analyze.title")}
              </h3>
              <p className="text-sm text-gray-400">
                {t("onboarding.welcome.card.analyze.desc")}
              </p>
            </div>

            {/* Card 3 */}
            <div className="bg-[#0a0d14] border border-gray-800 rounded-xl p-6 text-center hover:border-emerald-500/50 transition-all">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center mx-auto mb-4">
                <Zap className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="font-semibold mb-2">
                {t("onboarding.welcome.card.automate.title")}
              </h3>
              <p className="text-sm text-gray-400">
                {t("onboarding.welcome.card.automate.desc")}
              </p>
            </div>
          </div>

          {/* Continue Button */}
          <button
            onClick={() => navigate("/onboarding/connect")}
            className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-medium py-3 rounded-xl transition-all shadow-lg shadow-emerald-500/20"
          >
            {t("onboarding.welcome.button")}
          </button>
        </div>
      </div>
    </div>
  );
}

export default OnboardingWelcome;
