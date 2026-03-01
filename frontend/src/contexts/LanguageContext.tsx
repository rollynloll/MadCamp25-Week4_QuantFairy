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
    "nav.builder": "Strategy Builder",
    "nav.portfolio": "Portfolio",
    "nav.backtest": "Backtest",
    "nav.trading": "Trading",
    "nav.accountSettings": "Account Settings",
    "brand.tagline": "Strategy-first investing platform",
    "form.email": "Email",
    "form.password": "Password",
    "form.confirmPassword": "Confirm Password",
    "form.nickname": "Nickname",
    "form.optional": "(optional)",
    "form.emailPlaceholder": "you@example.com",
    "form.displayNamePlaceholder": "Your display name",
    "login.title": "Welcome back",
    "login.subtitle": "Log in to manage your strategies",
    "login.error.missing": "Please enter both email and password",
    "login.button": "Log in",
    "login.signupPrompt": "Don't have an account?",
    "login.signupCta": "Sign up",
    "signup.title": "Create your account",
    "signup.subtitle": "Start building your strategy-driven portfolio",
    "signup.error.required": "Please fill in all required fields",
    "signup.error.mismatch": "Passwords do not match",
    "signup.error.terms": "Please agree to the Terms & Privacy Policy",
    "signup.button": "Sign up",
    "signup.info":
      "You will connect a paper trading account in the next step.",
    "signup.loginPrompt": "Already have an account?",
    "signup.loginCta": "Log in",
    "signup.termsPrefix": "I agree to the",
    "signup.termsConnector": "&",
    "signup.termsLabel": "Terms",
    "signup.privacyLabel": "Privacy Policy",
    "signup.notice.checkEmail":
      "Check your email to confirm your account before continuing.",
    "verify.title": "Check your email",
    "verify.subtitle": "We sent a confirmation link to {email}.",
    "verify.subtitleNoEmail": "We sent a confirmation link to your email.",
    "verify.tip": "If you don't see it, check your spam folder.",
    "verify.resend": "Resend email",
    "verify.resendSuccess": "Verification email sent.",
    "verify.resendFail": "Failed to resend. Please try again.",
    "verify.backToLogin": "Back to login",
    "auth.error.config":
      "Supabase is not configured. Check VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.",
    "auth.error.invalidCredentials": "Invalid email or password.",
    "auth.error.invalidEmail": "Please enter a valid email address.",
    "auth.error.passwordTooShort": "Password must be at least 6 characters.",
    "auth.error.invalidPasswordChars":
      "Use only English letters, numbers, and special characters.",
    "auth.error.invalidNicknameChars":
      "Nickname can include Korean, English letters, numbers, and special characters.",
    "auth.error.emailNotConfirmed": "Please confirm your email to sign in.",
    "auth.error.userExists": "This email is already registered.",
    "auth.error.generic": "Authentication failed. Please try again.",
    "onboarding.step.welcome": "Welcome",
    "onboarding.step.connect": "Connect",
    "onboarding.step.setup": "Setup",
    "onboarding.welcome.title": "Welcome to QuantFairy",
    "onboarding.welcome.subtitle":
      "Select strategies. Backtest. Monitor automatically.",
    "onboarding.welcome.card.choose.title": "Choose a strategy",
    "onboarding.welcome.card.choose.desc":
      "Select from proven algorithmic strategies",
    "onboarding.welcome.card.analyze.title": "Analyze performance",
    "onboarding.welcome.card.analyze.desc":
      "Backtest and optimize your portfolio",
    "onboarding.welcome.card.automate.title": "Automate portfolio",
    "onboarding.welcome.card.automate.desc":
      "Execute trades automatically with confidence",
    "onboarding.welcome.button": "Continue",
    "onboarding.connect.title": "Connect Paper Trading Account",
    "onboarding.connect.subtitle":
      "Start with simulated capital before going live.",
    "onboarding.connect.status.notConnected": "Not connected",
    "onboarding.connect.status.connecting": "Connecting to Alpaca...",
    "onboarding.connect.status.connectedTitle": "Successfully Connected",
    "onboarding.connect.status.paperAccount": "Paper Account",
    "onboarding.connect.status.equity": "Equity",
    "onboarding.connect.status.failedTitle": "Connection Failed",
    "onboarding.connect.status.failedDesc":
      "Please try again or check your credentials",
    "onboarding.connect.error.loginRequired": "Please log in first.",
    "onboarding.connect.error.oauthFailed":
      "Failed to connect Alpaca. Please try again.",
    "onboarding.connect.button.connect": "Connect Paper Account",
    "onboarding.connect.button.retry": "Retry Connection",
    "onboarding.connect.link.create": "Create an Alpaca Paper Account →",
    "onboarding.connect.help": "Why is this required?",
    "onboarding.connect.button.continue": "Continue to Setup",
    "onboarding.setup.title": "Choose your starting setup",
    "onboarding.setup.subtitle": "Select a risk profile to get started",
    "onboarding.setup.risk.conservative": "Conservative",
    "onboarding.setup.risk.conservativeDesc": "Low risk, stable returns",
    "onboarding.setup.risk.conservativeTarget": "Target: 5-8% annual",
    "onboarding.setup.risk.balanced": "Balanced",
    "onboarding.setup.risk.balancedDesc": "Moderate risk and reward",
    "onboarding.setup.risk.balancedTarget": "Target: 10-15% annual",
    "onboarding.setup.risk.aggressive": "Aggressive",
    "onboarding.setup.risk.aggressiveDesc": "Higher risk, higher returns",
    "onboarding.setup.risk.aggressiveTarget": "Target: 18-25% annual",
    "onboarding.setup.recommendedTitle": "Recommended Strategies for {risk}",
    "onboarding.setup.strategy.meanReversion": "Mean Reversion",
    "onboarding.setup.strategy.meanReversionDesc":
      "Capitalizes on price corrections",
    "onboarding.setup.strategy.momentum": "Momentum Following",
    "onboarding.setup.strategy.momentumDesc": "Rides trending markets",
    "onboarding.setup.strategy.pairs": "Pairs Trading",
    "onboarding.setup.strategy.pairsDesc": "Statistical arbitrage",
    "onboarding.setup.button.complete": "Go to Portfolio",
    "account.title": "Account Settings",
    "account.subtitle": "Manage your profile and trading connections",
    "account.section.profile": "Profile",
    "account.section.brokers": "Broker Connections",
    "account.section.mode": "Trading Mode",
    "account.section.notifications": "Notifications",
    "account.button.changePassword": "Change Password",
    "account.button.logout": "Log out",
    "account.card.paper": "Paper Trading",
    "account.card.live": "Live Trading",
    "account.status.connected": "Connected",
    "account.status.disconnected": "Disconnected",
    "account.label.accountId": "Account ID",
    "account.label.equity": "Equity",
    "account.label.cash": "Cash",
    "account.button.reconnect": "Reconnect",
    "account.button.disconnect": "Disconnect",
    "account.warning.live":
      "Live trading executes real orders with real capital.",
    "account.button.connectLive": "Connect Live Account",
    "account.mode.paper": "Paper",
    "account.mode.live": "Live",
    "account.mode.current": "Current mode:",
    "account.mode.paperLabel": "Paper Trading",
    "account.mode.liveLabel": "Live Trading",
    "account.notification.tradeAlerts.title": "Trade Alerts",
    "account.notification.tradeAlerts.desc":
      "Get notified when trades are executed",
    "account.notification.riskAlerts.title": "Risk Alerts",
    "account.notification.riskAlerts.desc":
      "Warning when risk thresholds are exceeded",
    "account.notification.systemAlerts.title": "System Alerts",
    "account.notification.systemAlerts.desc":
      "Updates about platform maintenance and features",
    "account.modal.title": "Switch to Live Trading?",
    "account.modal.body":
      "You are about to enable live trading mode. All orders will be executed with real capital. This action cannot be undone automatically.",
    "account.modal.cancel": "Cancel",
    "account.modal.confirm": "Enable Live Mode",
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
    "nav.builder": "전략 빌더",
    "nav.portfolio": "포트폴리오",
    "nav.backtest": "백테스트",
    "nav.trading": "트레이딩",
    "nav.accountSettings": "계정 설정",
    "brand.tagline": "전략 중심 투자 플랫폼",
    "form.email": "이메일",
    "form.password": "비밀번호",
    "form.confirmPassword": "비밀번호 확인",
    "form.nickname": "닉네임",
    "form.optional": "(선택)",
    "form.emailPlaceholder": "you@example.com",
    "form.displayNamePlaceholder": "표시할 이름",
    "login.title": "다시 오신 것을 환영합니다",
    "login.subtitle": "전략 관리를 위해 로그인하세요",
    "login.error.missing": "이메일과 비밀번호를 모두 입력하세요",
    "login.button": "로그인",
    "login.signupPrompt": "계정이 없으신가요?",
    "login.signupCta": "회원가입",
    "signup.title": "계정을 만들어 주세요",
    "signup.subtitle": "전략 기반 포트폴리오를 시작하세요",
    "signup.error.required": "필수 항목을 모두 입력하세요",
    "signup.error.mismatch": "비밀번호가 일치하지 않습니다",
    "signup.error.terms": "이용약관 및 개인정보 처리방침에 동의해주세요",
    "signup.button": "회원가입",
    "signup.info": "다음 단계에서 모의 거래 계정을 연결합니다.",
    "signup.loginPrompt": "이미 계정이 있으신가요?",
    "signup.loginCta": "로그인",
    "signup.termsPrefix": "다음에 동의합니다",
    "signup.termsConnector": "및",
    "signup.termsLabel": "이용약관",
    "signup.privacyLabel": "개인정보 처리방침",
    "signup.notice.checkEmail":
      "계정을 확인하려면 이메일을 확인해주세요.",
    "verify.title": "이메일을 확인해주세요",
    "verify.subtitle": "{email}로 인증 링크를 보냈습니다.",
    "verify.subtitleNoEmail": "이메일로 인증 링크를 보냈습니다.",
    "verify.tip": "메일이 보이지 않으면 스팸함을 확인하세요.",
    "verify.resend": "인증 메일 재전송",
    "verify.resendSuccess": "인증 메일을 다시 보냈습니다.",
    "verify.resendFail": "재전송에 실패했습니다. 다시 시도해주세요.",
    "verify.backToLogin": "로그인으로 돌아가기",
    "auth.error.config":
      "Supabase 설정이 없습니다. VITE_SUPABASE_URL과 VITE_SUPABASE_ANON_KEY를 확인하세요.",
    "auth.error.invalidCredentials": "이메일 또는 비밀번호가 올바르지 않습니다.",
    "auth.error.invalidEmail": "올바른 이메일 형식을 입력하세요.",
    "auth.error.passwordTooShort": "비밀번호는 6자 이상이어야 합니다.",
    "auth.error.invalidPasswordChars":
      "영문, 숫자, 특수문자만 사용할 수 있습니다.",
    "auth.error.invalidNicknameChars":
      "닉네임은 한글, 영문, 숫자, 특수문자만 사용할 수 있습니다.",
    "auth.error.emailNotConfirmed":
      "이메일 인증 후 로그인할 수 있습니다.",
    "auth.error.userExists": "이미 등록된 이메일입니다.",
    "auth.error.generic": "인증에 실패했습니다. 다시 시도해주세요.",
    "onboarding.step.welcome": "환영",
    "onboarding.step.connect": "연결",
    "onboarding.step.setup": "설정",
    "onboarding.welcome.title": "QuantFairy에 오신 것을 환영합니다",
    "onboarding.welcome.subtitle": "전략 선택. 백테스트. 자동 모니터링.",
    "onboarding.welcome.card.choose.title": "전략 선택",
    "onboarding.welcome.card.choose.desc": "검증된 알고리즘 전략을 선택하세요",
    "onboarding.welcome.card.analyze.title": "성과 분석",
    "onboarding.welcome.card.analyze.desc":
      "백테스트로 포트폴리오를 최적화하세요",
    "onboarding.welcome.card.automate.title": "포트폴리오 자동화",
    "onboarding.welcome.card.automate.desc":
      "자동으로 거래를 실행하세요",
    "onboarding.welcome.button": "계속",
    "onboarding.connect.title": "모의 거래 계정 연결",
    "onboarding.connect.subtitle": "실거래 전에 모의 자본으로 시작하세요.",
    "onboarding.connect.status.notConnected": "연결되지 않음",
    "onboarding.connect.status.connecting": "Alpaca에 연결 중...",
    "onboarding.connect.status.connectedTitle": "연결되었습니다",
    "onboarding.connect.status.paperAccount": "모의 계정",
    "onboarding.connect.status.equity": "자산",
    "onboarding.connect.status.failedTitle": "연결 실패",
    "onboarding.connect.status.failedDesc":
      "다시 시도하거나 자격 증명을 확인하세요",
    "onboarding.connect.error.loginRequired": "먼저 로그인해주세요.",
    "onboarding.connect.error.oauthFailed":
      "Alpaca 연결에 실패했습니다. 다시 시도해주세요.",
    "onboarding.connect.button.connect": "모의 계정 연결",
    "onboarding.connect.button.retry": "재연결",
    "onboarding.connect.link.create": "Alpaca 모의 계정 만들기 →",
    "onboarding.connect.help": "왜 필요한가요?",
    "onboarding.connect.button.continue": "설정으로 계속",
    "onboarding.setup.title": "시작 설정을 선택하세요",
    "onboarding.setup.subtitle": "위험 성향을 선택하세요",
    "onboarding.setup.risk.conservative": "보수형",
    "onboarding.setup.risk.conservativeDesc": "낮은 위험, 안정적 수익",
    "onboarding.setup.risk.conservativeTarget": "목표: 연 5-8%",
    "onboarding.setup.risk.balanced": "균형형",
    "onboarding.setup.risk.balancedDesc": "중간 위험·수익",
    "onboarding.setup.risk.balancedTarget": "목표: 연 10-15%",
    "onboarding.setup.risk.aggressive": "공격형",
    "onboarding.setup.risk.aggressiveDesc": "높은 위험, 높은 수익",
    "onboarding.setup.risk.aggressiveTarget": "목표: 연 18-25%",
    "onboarding.setup.recommendedTitle": "{risk} 추천 전략",
    "onboarding.setup.strategy.meanReversion": "평균 회귀",
    "onboarding.setup.strategy.meanReversionDesc": "가격 되돌림을 활용",
    "onboarding.setup.strategy.momentum": "모멘텀 추종",
    "onboarding.setup.strategy.momentumDesc": "추세 시장을 추종",
    "onboarding.setup.strategy.pairs": "페어 트레이딩",
    "onboarding.setup.strategy.pairsDesc": "통계적 차익거래",
    "onboarding.setup.button.complete": "포트폴리오로 이동",
    "account.title": "계정 설정",
    "account.subtitle": "프로필과 거래 연결을 관리하세요",
    "account.section.profile": "프로필",
    "account.section.brokers": "브로커 연결",
    "account.section.mode": "거래 모드",
    "account.section.notifications": "알림",
    "account.button.changePassword": "비밀번호 변경",
    "account.button.logout": "로그아웃",
    "account.card.paper": "모의 거래",
    "account.card.live": "실거래",
    "account.status.connected": "연결됨",
    "account.status.disconnected": "연결 안 됨",
    "account.label.accountId": "계정 ID",
    "account.label.equity": "자산",
    "account.label.cash": "현금",
    "account.button.reconnect": "재연결",
    "account.button.disconnect": "연결 해제",
    "account.warning.live": "실거래는 실제 자본으로 주문을 실행합니다.",
    "account.button.connectLive": "실거래 계정 연결",
    "account.mode.paper": "모의",
    "account.mode.live": "실거래",
    "account.mode.current": "현재 모드:",
    "account.mode.paperLabel": "모의 거래",
    "account.mode.liveLabel": "실거래",
    "account.notification.tradeAlerts.title": "거래 알림",
    "account.notification.tradeAlerts.desc": "거래가 체결되면 알림을 받습니다",
    "account.notification.riskAlerts.title": "위험 알림",
    "account.notification.riskAlerts.desc":
      "위험 임계치를 초과하면 경고합니다",
    "account.notification.systemAlerts.title": "시스템 알림",
    "account.notification.systemAlerts.desc": "점검 및 기능 업데이트 소식",
    "account.modal.title": "실거래로 전환할까요?",
    "account.modal.body":
      "실거래 모드를 활성화하려고 합니다. 모든 주문이 실제 자본으로 실행됩니다. 이 작업은 자동으로 되돌릴 수 없습니다.",
    "account.modal.cancel": "취소",
    "account.modal.confirm": "실거래 모드 활성화",
  },
};

const LanguageContext = createContext<LanguageContextValue | undefined>(undefined);

function resolve(key: string, lang: Language) {
  return translations[lang][key] ?? key;
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState<Language>(() => {
    const stored = localStorage.getItem("language");
    return stored === "en" || stored === "ko" ? stored : "ko";
  });

  useEffect(() => {
    localStorage.setItem("language", language);
  }, [language]);

  const value = useMemo<LanguageContextValue>(() => {
    return {
      language,
      setLanguage,
      t: (key) => resolve(key, language),
      tr: (en, ko) => (language === "ko" ? ko : en),
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
