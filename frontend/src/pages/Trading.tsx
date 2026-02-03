import { useMemo, useState } from "react";
import TradingHeader from "@/components/trading/TradingHeader";
import OrderBook from "@/components/trading/OrderBook";
import OpenOrders from "@/components/trading/OpenOrders";
import GraphCurve from "@/components/trading/GraphCurve";
import PositionsTrade from "@/components/trading/PositionsTrade";

import { useTradingOrders } from "@/hooks/useTradingOrders";
import { useTradingPositions } from "@/hooks/useTradingPositions";
import { mapOrder } from "@/utils/tradingOrderUtils";
import { mapPosition } from "@/utils/tradingPositionUtils";

import { orderBook } from "@/data/trading.mock";

export default function Trading() {
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

  const selectedPosition = useMemo(
    () => positionsForTable.find((pos) => pos.symbol === selectedSymbol),
    [positionsForTable, selectedSymbol]
  );

  const basePriceBySymbol: Record<string, number> = {
    AAPL: 177.5,
    MSFT: 413.0,
    GOOGL: 143.0,
    TSLA: 245.2,
    NVDA: 621.4,
    AMD: 132.75,
  };

  const orderBookForSymbol = useMemo(() => {
    const basePrice = basePriceBySymbol[selectedSymbol] ?? 100;
    const bestBid = orderBook.bids[0]?.price ?? 0;
    const bestAsk = orderBook.asks[0]?.price ?? 0;
    const mid = bestBid && bestAsk ? (bestBid + bestAsk) / 2 : bestBid || bestAsk || 1;
    const scale = mid ? basePrice / mid : 1;

    return {
      bids: orderBook.bids.map((bid) => ({
        ...bid,
        price: +(bid.price * scale).toFixed(2),
      })),
      asks: orderBook.asks.map((ask) => ({
        ...ask,
        price: +(ask.price * scale).toFixed(2),
      })),
    };
  }, [orderBook, selectedSymbol]);

  return (
    <div className="space-y-6">
      <TradingHeader />

      <OpenOrders
        orders={openOrdersUi}
        filledOrders={filledOrdersUi}
        view={orderScope}
        onViewChange={setOrderScope}
      />

      <div className="grid grid-cols-[1fr_3fr] gap-6">
        <OrderBook orderBook={orderBookForSymbol} symbol={selectedSymbol} />
        <GraphCurve symbol={selectedSymbol} name={selectedPosition?.name} />
      </div>

      <PositionsTrade
        positions={positionsForTable}
        selectedSymbol={selectedSymbol}
        onSelect={setSelectedSymbol}
      />
    </div>
  );
}