import type { PortfolioSummaryResponse } from "@/types/portfolio";
import KPICard from "./KPICard";

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

  return (
    <div className="grid grid-cols-6 gap-3">
        <KPICard 
          label="Total Value" 
          value={formatUSD(account.equity)} 
        />
        <KPICard 
          label="Cash" 
          value={formatUSD(account.cash)} 
        />
        <KPICard 
          label="Today P&L" 
          value={`${account.today_pnl.value >= 0 ? "+" : ""}${formatUSD(account.today_pnl.value)}`}
          subvalue={formatPct(account.today_pnl.pct)}
          positive={account.today_pnl.value >= 0}
        />
        <KPICard
          label="Buying Power"
          value={formatUSD(account.buying_power)}
        />

        <KPICard
          label="Open Positions"
          value={String(account.open_positions.count)}
        />

        <KPICard
          label="Long / Short"
          value={`${account.open_positions.long}:${account.open_positions.short}`}
        />
      </div>
  );
}