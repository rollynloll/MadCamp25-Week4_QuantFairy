import { useMemo, useState } from "react";
import TradingHeader from "@/components/trading/TradingHeader";
import OrderBook from "@/components/trading/OrderBook";
import OpenOrders from "@/components/trading/OpenOrders";
import GraphCurve from "@/components/trading/GraphCurve";
import PositionsTrade from "@/components/trading/PositionsTrade";

import { useTradingOrders } from "@/hooks/useTradingOrders";
import { useTradingPositions } from "@/hooks/useTradingPositions";
import { useMarketStream } from "@/hooks/useMarketStream";
import { mapOrder } from "@/utils/tradingOrderUtils";
import { mapPosition } from "@/utils/tradingPositionUtils";
import type { OrderScope } from "@/api/trading";

export default function Trading() {
  const [orderScope, setOrderScope] = useState<OrderScope>("open");
  const [timeframe, setTimeframe] = useState<"1D" | "1W" | "1M" | "3M" | "1Y">("1D");
  const { items: openOrderItems } = useTradingOrders("open");
  const { items: filledOrderItems } = useTradingOrders("filled");
  const { openOrdersUi, filledOrdersUi } = useMemo(() => {
    const merged = new Map<string, ReturnType<typeof mapOrder>>();
    [...openOrderItems, ...filledOrderItems].forEach((order) => {
      merged.set(order.order_id, mapOrder(order));
    });
    const all = Array.from(merged.values());
    return {
      openOrdersUi: all.filter((order) => order.status !== "FILLED"),
      filledOrdersUi: all.filter((order) => order.status === "FILLED"),
    };
  }, [openOrderItems, filledOrderItems]);

  const { items: positionItems } = useTradingPositions();
  const positionsForTable = useMemo(() => positionItems.map(mapPosition), [positionItems]);

  const [selectedSymbol, setSelectedSymbol] = useState(
    positionsForTable[0]?.symbol ?? "AAPL"
  );

  const selectedPosition = useMemo(
    () => positionsForTable.find((pos) => pos.symbol === selectedSymbol),
    [positionsForTable, selectedSymbol]
  );

  const { orderBook, bars, midPrice, spread } = useMarketStream(selectedSymbol, timeframe);

  return (
    <div className="space-y-6">
      <TradingHeader />

      <OpenOrders
        orders={openOrdersUi}
        filledOrders={filledOrdersUi}
        allOrders={allOrdersUi}
        view={orderScope}
        onViewChange={setOrderScope}
      />

      <div className="grid grid-cols-[1fr_3fr] gap-6">
        <OrderBook
          orderBook={orderBook}
          symbol={selectedSymbol}
          midPrice={midPrice}
          spread={spread}
        />
        <GraphCurve
          symbol={selectedSymbol}
          name={selectedPosition?.name}
          bars={bars}
          timeframe={timeframe}
          onTimeframeChange={setTimeframe}
        />
      </div>

      <PositionsTrade
        positions={positionsForTable}
        selectedSymbol={selectedSymbol}
        onSelect={setSelectedSymbol}
      />
    </div>
  );
}
