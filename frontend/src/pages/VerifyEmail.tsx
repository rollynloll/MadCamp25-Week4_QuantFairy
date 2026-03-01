import { useMemo, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { Mail, RefreshCw } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { getSupabaseClient } from "@/lib/supabaseClient";

type LocationState = {
  email?: string;
};

export function VerifyEmail() {
  const { t } = useLanguage();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">(
    "idle"
  );

  const email = useMemo(() => {
    const fromState = (location.state as LocationState | null)?.email;
    return searchParams.get("email") || fromState || "";
  }, [location.state, searchParams]);

  const handleResend = async () => {
    if (!email) return;
    setStatus("loading");
    try {
      const supabase = getSupabaseClient();
      const { error } = await supabase.auth.resend({
        type: "signup",
        email,
      });
      if (error) {
        setStatus("error");
        return;
      }
      setStatus("success");
    } catch {
      setStatus("error");
    }
  };

  const subtitle = email
    ? t("verify.subtitle").replace("{email}", email)
    : t("verify.subtitleNoEmail");

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0d14] via-[#0d1117] to-[#0a0d14] flex items-center justify-center p-8">
      <div className="w-full max-w-[520px]">
        {/* Logo */}
        <div className="mb-12 text-center">
          <h1 className="text-4xl font-bold mb-3 bg-gradient-to-r from-emerald-400 to-teal-500 bg-clip-text text-transparent">
            QuantFairy
          </h1>
        </div>

        <div className="bg-[#0d1117] border border-gray-800 rounded-xl p-10 shadow-2xl text-center">
          <div className="w-14 h-14 rounded-full bg-emerald-500/10 flex items-center justify-center mx-auto mb-6">
            <Mail className="w-7 h-7 text-emerald-400" />
          </div>

          <h2 className="text-2xl font-semibold mb-3">{t("verify.title")}</h2>
          <p className="text-gray-400 mb-4">{subtitle}</p>
          <p className="text-sm text-gray-500 mb-8">{t("verify.tip")}</p>

          {status === "success" && (
            <div className="mb-4 text-sm text-emerald-300">
              {t("verify.resendSuccess")}
            </div>
          )}
          {status === "error" && (
            <div className="mb-4 text-sm text-red-400">
              {t("verify.resendFail")}
            </div>
          )}

          <div className="flex flex-col gap-3">
            <button
              type="button"
              onClick={handleResend}
              disabled={!email || status === "loading"}
              className={`w-full inline-flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-medium transition-all ${
                !email || status === "loading"
                  ? "bg-gray-800 text-gray-500 cursor-not-allowed"
                  : "bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20"
              }`}
            >
              <RefreshCw className={`w-4 h-4 ${status === "loading" ? "animate-spin" : ""}`} />
              {t("verify.resend")}
            </button>

            <Link
              to="/login"
              className="w-full py-3 rounded-xl text-sm font-medium text-gray-300 hover:text-white transition-colors"
            >
              {t("verify.backToLogin")}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default VerifyEmail;
