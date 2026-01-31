export default function OrderEntry() {
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">New Order</h2>
      <div className="space-y-4">
        <div>
          <label className="text-sm text-gray-400 mb-2 block">Symbol</label>
          <input
            type="text"
            placeholder="AAPL"
            className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm font-mono uppercase"
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <button className="py-2 bg-green-600/20 hover:bg-green-600/30 text-green-400 rounded text-sm font-medium transition-colors">
            BUY
          </button>
          <button className="py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded text-sm font-medium transition-colors">
            SELL
          </button>
        </div>
        <div>
          <label className="text-sm text-gray-400 mb-2 block">Order Type</label>
          <select className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm">
            <option>LIMIT</option>
            <option>MARKET</option>
            <option>STOP</option>
            <option>STOP LIMIT</option>
          </select>
        </div>
        <div>
          <label className="text-sm text-gray-400 mb-2 block">Quantity</label>
          <input
            type="number"
            placeholder="100"
            className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm font-mono"
          />
        </div>
        <div>
          <label className="text-sm text-gray-400 mb-2 block">Price</label>
          <input
            type="number"
            placeholder="178.25"
            step="0.01"
            className="w-full bg-[#0a0d14] border border-gray-800 rounded px-3 py-2 text-sm font-mono"
          />
        </div>
        <button className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition-colors">
          Place Order
        </button>
      </div>
    </div>
  );
}