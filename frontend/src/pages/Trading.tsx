import { useEffect, useMemo, useState } from "react";
import TradingHeader from "@/components/trading/TradingHeader";
import OrderBook from "@/components/trading/OrderBook";
import OpenOrders from "@/components/trading/OpenOrders";
import PositionsTrade from "@/components/trading/PositionsTrade";
import PriceChart from "@/components/trading/PriceChart";
import RecentTrades from "@/components/trading/RecentTrades";
import { useTradingOrders } from "@/hooks/useTradingOrders";
import { useTradingPositions } from "@/hooks/useTradingPositions";
import { useMarketStream } from "@/hooks/useMarketStream";
import { mapOrder } from "@/utils/tradingOrderUtils";
import { mapPosition } from "@/utils/tradingPositionUtils";
import { useLanguage } from "@/contexts/LanguageContext";

export default function Trading() {
  const { tr } = useLanguage();
  const [orderScope, setOrderScope] = useState<"open" | "filled">("open");
  const { items: openOrderItems } = useTradingOrders("open");
  const { items: filledOrderItems } = useTradingOrders("filled");
  const openOrdersUi = openOrderItems.map(mapOrder);
  const filledOrdersUi = filledOrderItems.map(mapOrder);

  const { items: positionItems } = useTradingPositions();
  const positionsForTable = positionItems.map(mapPosition);

  const [selectedSymbol, setSelectedSymbol] = useState(
    positionsForTable[0]?.symbol ?? "AAPL"
  );

  useEffect(() => {
    if (!positionsForTable.length) return;
    if (!positionsForTable.find((pos) => pos.symbol === selectedSymbol)) {
      setSelectedSymbol(positionsForTable[0].symbol);
    }
  }, [positionsForTable, selectedSymbol]);

  const selectedPosition = useMemo(
    () => positionsForTable.find((pos) => pos.symbol === selectedSymbol),
    [positionsForTable, selectedSymbol]
  );

  const { orderBook, trades, bars, midPrice, spread, status } = useMarketStream(selectedSymbol);

  return (
    <div className="space-y-6">
      <TradingHeader />

      <OpenOrders
        orders={openOrdersUi}
        filledOrders={filledOrdersUi}
        view={orderScope}
        onViewChange={setOrderScope}
      />

      <div className="flex flex-wrap items-center gap-3">
        <label className="text-xs text-gray-500">{tr("Symbol", "종목")}</label>
        <input
          value={selectedSymbol}
          onChange={(e) => setSelectedSymbol(e.target.value.toUpperCase())}
          className="bg-[#0a0d14] border border-gray-800 rounded px-3 py-1.5 text-sm font-mono w-32"
        />
        <span className="text-xs text-gray-500">
          {tr("Stream", "스트림")}: {status}
        </span>
        {selectedPosition?.name && (
          <span className="text-xs text-gray-500">{selectedPosition.name}</span>
        )}
      </div>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 xl:col-span-7">
          <PriceChart symbol={selectedSymbol} bars={bars} lastPrice={midPrice} status={status} />
        </div>
        <div className="col-span-12 xl:col-span-5 space-y-6">
          <OrderBook
            orderBook={orderBook}
            symbol={selectedSymbol}
            midPrice={midPrice}
            spread={spread}
          />
          <RecentTrades trades={trades} />
        </div>
      </div>

      <PositionsTrade
        positions={positionsForTable}
        selectedSymbol={selectedSymbol}
        onSelect={setSelectedSymbol}
      />
    </div>
  );
}
