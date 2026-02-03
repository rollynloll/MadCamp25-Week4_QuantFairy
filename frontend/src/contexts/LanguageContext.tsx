import { createContext, useContext, useEffect, useMemo, useState } from "react";

type Language = "en" | "ko";

type LanguageContextValue = {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
  tr: (en: string, ko: string) => string;
};

const translations: Record<Language, Record<string, string>> = {
  en: {
    "header.paper": "Paper",
    "header.live": "LIVE",
    "header.liveConfirm": "Switch to live mode?",
    "header.liveEnabled": "Live trading enabled",
    "header.killSwitchOn": "Kill Switch On",
    "header.killSwitchEnable": "Kill Switch",
    "header.connected": "Connected",
    "header.disconnected": "Unconnected",
    "header.run": "Run",
    "header.stop": "Stop",
    "header.queued": "Queued",
    "header.accountBalance": "Account Balance",
    "header.langEn": "EN",
    "header.langKo": "KO",
    "nav.dashboard": "Dashboard",
    "nav.strategies": "Strategies",
    "nav.portfolio": "Portfolio",
    "nav.backtest": "Backtest",
    "nav.trading": "Trading",
  },
  ko: {
    "header.paper": "모의",
    "header.live": "실전",
    "header.liveConfirm": "실전 모드로 전환할까요?",
    "header.liveEnabled": "실전 거래 활성화",
    "header.killSwitchOn": "킬 스위치 켬",
    "header.killSwitchEnable": "킬 스위치",
    "header.connected": "연결됨",
    "header.disconnected": "연결 끊김",
    "header.run": "실행",
    "header.stop": "중지",
    "header.queued": "대기 중",
    "header.accountBalance": "계좌 잔고",
    "header.langEn": "EN",
    "header.langKo": "KO",
    "nav.dashboard": "대시보드",
    "nav.strategies": "전략",
    "nav.portfolio": "포트폴리오",
    "nav.backtest": "백테스트",
    "nav.trading": "트레이딩",
  },
};

const LanguageContext = createContext<LanguageContextValue | undefined>(undefined);

function resolve(key: string, lang: Language) {
  return translations[lang][key] ?? key;
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState<Language>(() => {
    const stored = localStorage.getItem("language");
    return stored === "en" || stored === "ko" ? stored : "en";
  });

  useEffect(() => {
    localStorage.setItem("language", language);
  }, [language]);

  const value = useMemo<LanguageContextValue>(() => {
    return {
      language,
      setLanguage,
      t: (key) => resolve(key, language),
      tr: (en, ko) => (language === "en" ? en : ko),
    };
  }, [language]);

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error("useLanguage must be used within LanguageProvider");
  }
  return ctx;
}
