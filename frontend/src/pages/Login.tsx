import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { getSupabaseClient } from "@/lib/supabaseClient";

export function Login() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const minPasswordLength = 6;
  const invalidPasswordCharsMessage = t("auth.error.invalidPasswordChars");
  const sanitizePasswordInput = (value: string) =>
    value.replace(/[^\x21-\x7E]/g, "");

  const resolveAuthError = (message: string) => {
    const normalized = message.toLowerCase();
    if (normalized.includes("invalid login credentials")) {
      return t("auth.error.invalidCredentials");
    }
    if (normalized.includes("email not confirmed")) {
      return t("auth.error.emailNotConfirmed");
    }
    return message;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email || !password) {
      setError(t("login.error.missing"));
      return;
    }

    if (!/^[\x21-\x7E]+$/.test(password)) {
      setError(t("auth.error.invalidPasswordChars"));
      return;
    }

    const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
    if (!emailValid) {
      setError(t("auth.error.invalidEmail"));
      return;
    }

    if (password.length < minPasswordLength) {
      setError(t("auth.error.passwordTooShort"));
      return;
    }

    setIsSubmitting(true);
    try {
      const supabase = getSupabaseClient();
      const { error: authError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (authError) {
        setError(resolveAuthError(authError.message));
        return;
      }
      navigate("/");
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
      <div className="w-full max-w-[600px]">
        {/* Logo and Tagline */}
        <div className="mb-16 text-center">
          <h1 className="text-5xl font-bold mb-3 bg-gradient-to-r from-emerald-400 to-teal-500 bg-clip-text text-transparent">
            QuantFairy
          </h1>
          <p className="text-base text-gray-400">{t("brand.tagline")}</p>
        </div>

        {/* Auth Card */}
        <div className="bg-[#0d1117] border border-gray-800 rounded-xl p-12 shadow-2xl">
          <div className="mb-10">
            <h2 className="text-4xl font-semibold mb-3">
              {t("login.title")}
            </h2>
            <p className="text-base text-gray-400">{t("login.subtitle")}</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-8">
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
                value={email}
                disabled={isSubmitting}
                onChange={(e) => setEmail(e.target.value)}
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
                  value={password}
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
                    setPassword(sanitized);
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

            {/* Error Message */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/50 rounded-xl px-4 py-4 text-base text-red-400">
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
              {t("login.button")}
            </button>
          </form>

          {/* Sign Up Link */}
          <div className="mt-8 text-center">
            <p className="text-base text-gray-400">
              {t("login.signupPrompt")}{" "}
              <Link
                to="/signup"
                className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors"
              >
                {t("login.signupCta")}
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;
