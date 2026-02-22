import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

export function Signup() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    nickname: "",
    agreeToTerms: false,
  });
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Validation
    if (!formData.email || !formData.password || !formData.confirmPassword) {
      setError(t("signup.error.required"));
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError(t("signup.error.mismatch"));
      return;
    }

    if (!formData.agreeToTerms) {
      setError(t("signup.error.terms"));
      return;
    }

    // Mock successful signup - navigate to onboarding
    navigate("/onboarding/welcome");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0d14] via-[#0d1117] to-[#0a0d14] flex items-center justify-center p-8">
      {/* Main Container */}
      <div className="w-full max-w-[560px]">
        {/* Logo and Tagline */}
        <div className="mb-12 text-center">
          <h1 className="text-4xl font-bold mb-3 bg-gradient-to-r from-emerald-400 to-teal-500 bg-clip-text text-transparent">
            QuantFairy
          </h1>
          <p className="text-base text-gray-400">{t("brand.tagline")}</p>
        </div>

        {/* Signup Card */}
        <div className="bg-[#0d1117] border border-gray-800 rounded-xl p-10 shadow-2xl">
          <div className="mb-8">
            <h2 className="text-3xl font-semibold mb-2">
              {t("signup.title")}
            </h2>
            <p className="text-base text-gray-400">{t("signup.subtitle")}</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email Input */}
            <div>
              <label
                htmlFor="email"
                className="block text-base font-medium text-gray-300 mb-3"
              >
                {t("form.email")}
              </label>
              <input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
                placeholder={t("form.emailPlaceholder")}
                className="w-full bg-[#0a0d14] border border-gray-800 rounded-xl px-6 py-4 text-base focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
              />
            </div>

            {/* Password Input */}
            <div>
              <label
                htmlFor="password"
                className="block text-base font-medium text-gray-300 mb-3"
              >
                {t("form.password")}
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={formData.password}
                  onChange={(e) =>
                    setFormData({ ...formData, password: e.target.value })
                  }
                  placeholder="••••••••"
                  className="w-full bg-[#0a0d14] border border-gray-800 rounded-xl px-6 py-4 pr-12 text-base focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>

            {/* Confirm Password Input */}
            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-base font-medium text-gray-300 mb-3"
              >
                {t("form.confirmPassword")}
              </label>
              <div className="relative">
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  value={formData.confirmPassword}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      confirmPassword: e.target.value,
                    })
                  }
                  placeholder="••••••••"
                  className="w-full bg-[#0a0d14] border border-gray-800 rounded-xl px-6 py-4 pr-12 text-base focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                >
                  {showConfirmPassword ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>

            {/* Optional Nickname */}
            <div>
              <label
                htmlFor="nickname"
                className="block text-base font-medium text-gray-300 mb-3"
              >
                {t("form.nickname")} {" "}
                <span className="text-gray-500">{t("form.optional")}</span>
              </label>
              <input
                id="nickname"
                type="text"
                value={formData.nickname}
                onChange={(e) =>
                  setFormData({ ...formData, nickname: e.target.value })
                }
                placeholder={t("form.displayNamePlaceholder")}
                className="w-full bg-[#0a0d14] border border-gray-800 rounded-xl px-6 py-4 text-base focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
              />
            </div>

            {/* Terms Checkbox */}
            <div className="flex items-start gap-3">
              <input
                id="terms"
                type="checkbox"
                checked={formData.agreeToTerms}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    agreeToTerms: e.target.checked,
                  })
                }
                className="mt-1 w-4 h-4 rounded border-gray-800 bg-[#0a0d14] text-emerald-500 focus:ring-2 focus:ring-emerald-500/50"
              />
              <label htmlFor="terms" className="text-sm text-gray-400">
                {t("signup.termsPrefix")} {" "}
                <a href="#" className="text-emerald-400 hover:text-emerald-300">
                  {t("signup.termsLabel")}
                </a>{" "}
                {t("signup.termsConnector")} {" "}
                <a href="#" className="text-emerald-400 hover:text-emerald-300">
                  {t("signup.privacyLabel")}
                </a>
              </label>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/50 rounded-xl px-4 py-3 text-sm text-red-400">
                {error}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-medium py-4 rounded-xl transition-all shadow-lg shadow-emerald-500/20 text-base"
            >
              {t("signup.button")}
            </button>

            {/* Info Text */}
            <p className="text-sm text-gray-500 text-center">
              {t("signup.info")}
            </p>
          </form>

          {/* Login Link */}
          <div className="mt-6 text-center">
            <p className="text-base text-gray-400">
              {t("signup.loginPrompt")} {" "}
              <Link
                to="/login"
                className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors"
              >
                {t("signup.loginCta")}
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Signup;
