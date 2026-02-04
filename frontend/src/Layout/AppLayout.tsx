import Header from "./Header";
import SideBar from "./SideBar";
import { useTradingMode } from "@/hooks/useTradingMode";
import { useDashboardContext } from "@/contexts/DashboardContext";

interface AppLayoutProps {
  readonly children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const { mode, changeMode } = useTradingMode("paper");
  const { data } = useDashboardContext();

  return (
    <div className="flex h-screen bg-[#0a0d14] text-gray-100">
      <SideBar />
      <div className="flex flex-col flex-1">
        <Header
          mode={mode} 
          onModeChange={changeMode} 
          botState={data?.bot.state ?? "stopped"}
        />
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  );
}
