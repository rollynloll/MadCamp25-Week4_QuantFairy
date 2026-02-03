import type { OrderBook as OrderBookData } from "@/types/trading";
import { useLanguage } from "@/contexts/LanguageContext";

type Props = {
  orderBook: OrderBookData;
  symbol?: string;
};

export default function OrderBook({ orderBook, symbol }: Props) {
  const { tr } = useLanguage();
  const bestBid = orderBook.bids[0]?.price ?? null;
  const bestAsk = orderBook.asks[0]?.price ?? null;
  const mid =
    bestBid !== null && bestAsk !== null ? (bestBid + bestAsk) / 2 : bestBid ?? bestAsk ?? null;
  const spread =
    bestBid !== null && bestAsk !== null ? bestAsk - bestBid : null;

  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">{tr("Order Book", "호가")}</h2>
        <div className="text-sm text-gray-400 font-mono">{symbol ?? "AAPL"}</div>
      </div>
      <div className="space-y-4">
        <div>
          <div className="text-xs text-gray-500 mb-2 flex justify-between px-2">
            <span>{tr("Price", "가격")}</span>
            <span>{tr("Size", "수량")}</span>
          </div>
          <div className="space-y-1">
            {[...orderBook.asks].reverse().map((ask, i) => (
              <div
                key={i}
                className="flex justify-between items-center text-sm py-1 px-2 rounded hover:bg-red-600/10"
              >
                <span className="font-mono text-red-400">
                  {ask.price.toFixed(2)}
                </span>
                <span className="font-mono text-gray-400">{ask.size}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="py-2 bg-gray-800/50 rounded text-center">
          <div className="text-lg font-mono font-semibold">
            {mid !== null ? mid.toFixed(2) : "--"}
          </div>
          <div className="text-xs text-gray-500">
            {tr("Spread", "호가 차이")}: {spread !== null ? `$${spread.toFixed(2)}` : "--"}
          </div>
        </div>

        <div>
          <div className="space-y-1">
            {orderBook.bids.map((bid, i) => (
              <div
                key={i}
                className="flex justify-between items-center text-sm py-1 px-2 rounded hover:bg-green-600/10"
              >
                <span className="font-mono text-green-400">
                  {bid.price.toFixed(2)}
                </span>
                <span className="font-mono text-gray-400">{bid.size}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
