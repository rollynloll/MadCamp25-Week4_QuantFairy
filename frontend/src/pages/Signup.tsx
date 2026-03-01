import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { getSupabaseClient } from "@/lib/supabaseClient";

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
  const [isSubmitting, setIsSubmitting] = useState(false);
  const minPasswordLength = 6;
  const invalidPasswordCharsMessage = t("auth.error.invalidPasswordChars");
  const invalidNicknameCharsMessage = t("auth.error.invalidNicknameChars");
  const sanitizePasswordInput = (value: string) =>
    value.replace(/[^\x21-\x7E]/g, "");
  const sanitizeNicknameInput = (value: string) =>
    value.replace(/[^\x20-\x7E\u1100-\u11FF\u3130-\u318F\uAC00-\uD7A3]/g, "");

  const resolveAuthError = (message: string) => {
    const normalized = message.toLowerCase();
    if (normalized.includes("user already registered")) {
      return t("auth.error.userExists");
    }
    if (normalized.includes("password should be at least")) {
      return t("auth.error.passwordTooShort");
    }
    return message;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!formData.email || !formData.password || !formData.confirmPassword) {
      setError(t("signup.error.required"));
      return;
    }

    if (
      formData.nickname &&
      /[^\x20-\x7E\u1100-\u11FF\u3130-\u318F\uAC00-\uD7A3]/.test(
        formData.nickname
      )
    ) {
      setError(t("auth.error.invalidNicknameChars"));
      return;
    }

    if (!/^[\x21-\x7E]+$/.test(formData.password)) {
      setError(t("auth.error.invalidPasswordChars"));
      return;
    }

    const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(
      formData.email.trim()
    );
    if (!emailValid) {
      setError(t("auth.error.invalidEmail"));
      return;
    }

    if (formData.password.length < minPasswordLength) {
      setError(t("auth.error.passwordTooShort"));
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

    setIsSubmitting(true);
    try {
      const supabase = getSupabaseClient();
      const metadata = formData.nickname
        ? { nickname: formData.nickname, display_name: formData.nickname }
        : undefined;
      const { data, error: authError } = await supabase.auth.signUp({
        email: formData.email,
        password: formData.password,
        options: {
          data: metadata,
          emailRedirectTo: `${window.location.origin}/onboarding/welcome`,
        },
      });

      if (authError) {
        setError(resolveAuthError(authError.message));
        return;
      }

      if (data.session) {
        navigate("/onboarding/welcome");
        return;
      }

      navigate(`/auth/verify?email=${encodeURIComponent(formData.email)}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "";
      setError(
        message.includes("Missing Supabase env vars")
          ? t("auth.error.config")
          : t("auth.error.generic")
      );
    } finally {
      setIsSubmitting(false);
    }
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
                disabled={isSubmitting}
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
                  disabled={isSubmitting}
                  onChange={(e) => {
                    const rawValue = e.target.value;
                    const sanitized = sanitizePasswordInput(rawValue);
                    if (rawValue !== sanitized) {
                      if (error !== invalidPasswordCharsMessage) {
                        setError(invalidPasswordCharsMessage);
                      }
                    } else if (error === invalidPasswordCharsMessage) {
                      setError("");
                    }
                    setFormData({ ...formData, password: sanitized });
                  }}
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
                  disabled={isSubmitting}
                  onChange={(e) => {
                    const rawValue = e.target.value;
                    const sanitized = sanitizePasswordInput(rawValue);
                    if (rawValue !== sanitized) {
                      if (error !== invalidPasswordCharsMessage) {
                        setError(invalidPasswordCharsMessage);
                      }
                    } else if (error === invalidPasswordCharsMessage) {
                      setError("");
                    }
                    setFormData({
                      ...formData,
                      confirmPassword: sanitized,
                    });
                  }}
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
                disabled={isSubmitting}
                onChange={(e) => {
                  const rawValue = e.target.value;
                  const sanitized = sanitizeNicknameInput(rawValue);
                  if (rawValue !== sanitized) {
                    if (error !== invalidNicknameCharsMessage) {
                      setError(invalidNicknameCharsMessage);
                    }
                  } else if (error === invalidNicknameCharsMessage) {
                    setError("");
                  }
                  setFormData({ ...formData, nickname: sanitized });
                }}
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
                disabled={isSubmitting}
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
              disabled={isSubmitting}
              className={`w-full font-medium py-4 rounded-xl transition-all shadow-lg shadow-emerald-500/20 text-base ${
                isSubmitting
                  ? "bg-gray-800 text-gray-500 cursor-not-allowed"
                  : "bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white"
              }`}
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
