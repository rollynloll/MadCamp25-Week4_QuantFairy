import type { PortfolioSummaryResponse } from "@/types/portfolio";
import KPICard from "./KPICard";
import { useLanguage } from "@/contexts/LanguageContext";

function formatUSD(value: number) {
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function formatPct(value: number) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export default function PortfolioSummary({ 
  summary 
}: {
  summary: PortfolioSummaryResponse;
}) {
  const { account } = summary;
  const { tr } = useLanguage();

  return (
    <div className="grid grid-cols-6 gap-3">
        <KPICard 
          label={tr("Total Value", "총 자산")} 
          value={formatUSD(account.equity)} 
        />
        <KPICard 
          label={tr("Cash", "현금")} 
          value={formatUSD(account.cash)} 
        />
        <KPICard 
          label={tr("Today P&L", "오늘 손익")} 
          value={`${account.today_pnl.value >= 0 ? "+" : ""}${formatUSD(account.today_pnl.value)}`}
          subvalue={formatPct(account.today_pnl.pct)}
          positive={account.today_pnl.value >= 0}
        />
        <KPICard
          label={tr("Buying Power", "매수 가능 금액")}
          value={formatUSD(account.buying_power)}
        />

        <KPICard
          label={tr("Open Positions", "보유 포지션")}
          value={String(account.open_positions.count)}
        />

        <KPICard
          label={tr("Long / Short", "롱 / 숏")}
          value={`${account.open_positions.long}:${account.open_positions.short}`}
        />
      </div>
  );
}
