import { useState } from "react";
import TradingHeader from "@/components/trading/TradingHeader";
import OrderEntry from "@/components/trading/OrderEntry";
import OrderBook from "@/components/trading/OrderBook";
import RecentTrades from "@/components/trading/RecentTrades";
import OpenOrders from "@/components/trading/OpenOrders";
import PriceChart from "@/components/trading/PriceChart";
import { openOrders } from "@/data/trading.mock";
import { useMarketStream } from "@/hooks/useMarketStream";
import { useLanguage } from "@/contexts/LanguageContext";

export default function Trading() {
  const { tr } = useLanguage();
  const [symbol, setSymbol] = useState("AAPL");
  const { orderBook, trades, bars, midPrice, spread, status } = useMarketStream(symbol);

  return (
    <div className="space-y-6">
      <TradingHeader />

      <div className="flex flex-wrap items-center gap-3">
        <label className="text-xs text-gray-500">{tr("Symbol", "종목")}</label>
        <input
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          className="bg-[#0a0d14] border border-gray-800 rounded px-3 py-1.5 text-sm font-mono w-32"
        />
        <span className="text-xs text-gray-500">
          {tr("Stream", "스트림")}: {status}
        </span>
      </div>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 xl:col-span-8">
          <PriceChart symbol={symbol} bars={bars} lastPrice={midPrice} status={status} />
        </div>
        <div className="col-span-12 xl:col-span-4">
          <OrderBook orderBook={orderBook} symbol={symbol} midPrice={midPrice} spread={spread} />
        </div>
        <div className="col-span-12 xl:col-span-4">
          <OrderEntry />
        </div>
        <div className="col-span-12 xl:col-span-4">
          <RecentTrades trades={trades} />
        </div>
        <div className="col-span-12 xl:col-span-4">
          <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6 h-full">
            <div className="text-sm font-semibold mb-2">{tr("Notes", "노트")}</div>
            <div className="text-xs text-gray-500">
              {tr(
                "Order book shows top-of-book quotes streamed via Alpaca Market Data.",
                "호가는 Alpaca 실시간 호가(Top-of-book) 스트림을 표시합니다."
              )}
            </div>
          </div>
        </div>
      </div>

      <OpenOrders orders={openOrders} />
    </div>
  );
}
