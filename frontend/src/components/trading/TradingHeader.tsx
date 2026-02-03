import { useLanguage } from "@/contexts/LanguageContext";

export default function TradingHeader() {
  const { tr } = useLanguage();
  return (
    <div>
      <h1 className="text-2xl font-semibold mb-1">{tr("Trading", "트레이딩")}</h1>
      <p className="text-sm text-gray-400">
        {tr("Real-time order execution and market data", "실시간 주문 실행 및 시장 데이터")}
      </p>
    </div>
  );
}
