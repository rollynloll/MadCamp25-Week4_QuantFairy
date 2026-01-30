import TradingHeader from "@/components/trading/TradingHeader";
import OrderEntry from "@/components/trading/OrderEntry";
import OrderBook from "@/components/trading/OrderBook";
import RecentTrades from "@/components/trading/RecentTrades";
import OpenOrders from "@/components/trading/OpenOrders";
import {
  orderBook,
  recentTrades,
  openOrders,
} from "@/data/trading.mock";

export default function Trading() {
  return (
    <div className="space-y-6">
      <TradingHeader />

      <div className="grid grid-cols-3 gap-6">
        <OrderEntry />
        <OrderBook orderBook={orderBook} />
        <RecentTrades trades={recentTrades} />
      </div>

      <OpenOrders orders={openOrders} />
    </div>
  );
}