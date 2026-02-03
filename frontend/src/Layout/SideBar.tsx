import { NavLink } from "react-router-dom";
import {
  Activity,
  Briefcase,
  LayoutDashboard,
  LineChart,
  Layers,
  TrendingUp,
} from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface NavItem {
  path: string;
  labelKey: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { path: "/", labelKey: "nav.dashboard", icon: LayoutDashboard },
  { path: "/strategies", labelKey: "nav.strategies", icon: TrendingUp },
  { path: "/builder", labelKey: "nav.builder", icon: Layers },
  { path: "/portfolio", labelKey: "nav.portfolio", icon: Briefcase },
  { path: "/backtest", labelKey: "nav.backtest", icon: LineChart },
  { path: "/trading", labelKey: "nav.trading", icon: Activity },
];

export default function SideBar() {
  const { t } = useLanguage();
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
                  <span>{t(item.labelKey)}</span>
                </>
              )}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
