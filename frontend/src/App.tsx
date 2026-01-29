import { Route, BrowserRouter as Router, Routes } from "react-router-dom";
import Home from "./pages/Home";
import Portfolio from "./pages/Portfolio";
import Strategies from "./pages/Strategies";
import Backtest from "./pages/Backtest";
import Trading from "./pages/Trading";
import AppLayout from "./Layout/AppLayout";

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/strategies" element={<Strategies />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/backtest" element={<Backtest />} />
          <Route path="/trading" element={<Trading />} />
          <Route path="*" element={<h1>404 Not Found</h1>} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
