import { Route, BrowserRouter as Router, Routes } from "react-router-dom";
import Home from "./pages/Home";
import Portfolio from "./pages/Portfolio";
import Strategies from "./pages/Strategies";
import Backtest from "./pages/Backtest";
import Trading from "./pages/Trading";
import StrategyPage from "./pages/StrategyPage";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import VerifyEmail from "./pages/VerifyEmail";
import OnboardingWelcome from "./pages/OnboardingWelcome";
import OnboardingConnect from "./pages/OnboardingConnect";
import OnboardingSetup from "./pages/OnboardingSetup";
import Account from "./pages/Account";
import AppLayout from "./Layout/AppLayout";
import { LanguageProvider } from "./contexts/LanguageContext";
import { DashboardProvider } from "./contexts/DashboardContext";
import { ThemeProvider } from "./contexts/ThemeContext";

function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <DashboardProvider>
          <Router>
            <Routes>
              {/* Auth Routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/auth/verify" element={<VerifyEmail />} />
              <Route path="/onboarding/welcome" element={<OnboardingWelcome />} />
              <Route path="/onboarding/connect" element={<OnboardingConnect />} />
              <Route path="/onboarding/setup" element={<OnboardingSetup />} />
              
              {/* Main App Routes */}
              <Route
                path="/*"
                element={
                  <AppLayout>
                    <Routes>
                      <Route path="/" element={<Home />} />
                      <Route path="/strategies" element={<Strategies />} />
                      <Route path="/builder" element={<StrategyPage />} />
                      <Route path="/portfolio" element={<Portfolio />} />
                      <Route path="/account" element={<Account />} />
                      <Route path="/backtest" element={<Backtest />} />
                      <Route path="/trading" element={<Trading />} />
                      <Route path="*" element={<h1>404 Not Found</h1>} />
                    </Routes>
                  </AppLayout>
                }
              />
            </Routes>
          </Router>
        </DashboardProvider>
      </LanguageProvider>
    </ThemeProvider>
  );
}

export default App;
