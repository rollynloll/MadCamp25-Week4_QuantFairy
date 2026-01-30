export interface OrderBookLevel {
  price: number;
  size: number;
  total: number;
}

export interface OrderBook {
  bids: OrderBookLevel[];
  asks: OrderBookLevel[];
}

export interface RecentTrade {
  time: string;
  price: number;
  size: number;
  side: "buy" | "sell";
}

export interface OpenOrder {
  id: string;
  symbol: string;
  side: "BUY" | "SELL";
  type: "LIMIT" | "MARKET" | "STOP" | "STOP LIMIT";
  qty: number;
  filled: number;
  price: number;
  status: "PENDING" | "PARTIAL";
  strategy: string;
}
