import { useState } from "react";
import Header from "./Header";
import SideBar from "./SideBar";
import { useTradingMode } from "@/hooks/useTradingMode";
import { useDashboard } from "@/hooks/useDashboard";
import type { Range } from "@/types/dashboard";

interface AppLayoutProps {
  readonly children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const { mode, changeMode } = useTradingMode("paper");

  const [range] = useState<Range>("1M");
  const { data } = useDashboard(range);

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
