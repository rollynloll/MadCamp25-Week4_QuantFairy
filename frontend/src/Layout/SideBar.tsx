import { NavLink } from "react-router-dom";
import {
  Activity,
  Briefcase,
  LayoutDashboard,
  LineChart,
  TrendingUp,
} from "lucide-react";
import { useBotControl } from "@/hooks/useBotControl";

interface NavItem {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { path: "/", label: "Dashboard", icon: LayoutDashboard },
  { path: "/strategies", label: "Strategies", icon: TrendingUp },
  { path: "/portfolio", label: "Portfolio", icon: Briefcase },
  { path: "/backtest", label: "Backtest", icon: LineChart },
  { path: "/trading", label: "Trading", icon: Activity },
];

export default function SideBar() {
  const { loading: botLoading, start, stop, runNow } = useBotControl("stopped");

  return (
    <aside className="w-64 bg-[#0d1117] border-r border-gray-800 flex flex-col">
      <div className="h-16 flex items-center px-6 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center">
            <Activity className="w-5 h-5" />
          </div>
          <span className="text-lg font-semibold">QuantTrade</span>
        </div>
      </div>

      <nav className="flex-1 py-6">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-6 py-3 text-sm transition-colors ${
                  isActive
                    ? "bg-blue-600/10 text-blue-400 border-r-2 border-blue-500"
                    : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className={`w-5 h-5 ${isActive ? "text-blue-400" : ""}`} />
                  <span>{item.label}</span>
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="p-6 border-t border-gray-800">
        <div className="flex flex-col gap-3 text-xs text-gray-500">

          <button onClick={start} disabled={botLoading}>Start</button>
          <button onClick={stop} disabled={botLoading}>Stop</button>
          <button onClick={runNow} disabled={botLoading}>Run Now</button>

        </div>
      </div>
    </aside>
  );
}
