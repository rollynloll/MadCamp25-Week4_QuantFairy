import type { OrderBook as OrderBookData } from "@/types/trading";

export default function OrderBook({ orderBook }: { orderBook: OrderBookData }) {
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Order Book</h2>
        <div className="text-sm text-gray-400 font-mono">AAPL</div>
      </div>
      <div className="space-y-4">
        <div>
          <div className="text-xs text-gray-500 mb-2 flex justify-between px-2">
            <span>Price</span>
            <span>Size</span>
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
          <div className="text-lg font-mono font-semibold">178.25</div>
          <div className="text-xs text-gray-500">Spread: $0.01</div>
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
