import KPICard from "./KPICard";

export default function PortfolioSummary() {
  return (
    <div className="grid grid-cols-6 gap-3">
        <KPICard label="Total Value" value="$115,600" />
        <KPICard label="Cash" value="$14,450" />
        <KPICard label="Today P&L" value="+$1,245" subvalue="+1.08%" positive />
        <KPICard label="Unrealized P&L" value="+$702" positive />
        <KPICard label="Open Positions" value="5" />
        <KPICard label="Long/Short" value="4:1" />
      </div>
  );
}