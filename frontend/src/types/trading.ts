export interface OrderBookLevel {
  price: number;
  size: number;
  total: number;
}

export type OrderStatus = "new" | "accepted" | "partially_filled" | "filled" | "canceled" | "rejected" | "expired";

export type OrderSide = "buy" | "sell";
export type OrderType = "limit" | "market" | "stop" | "stop_limit";

export interface TradingOrder {
  order_id: string;
  submitted_at: string;
  symbol: string;
  side: OrderSide;
  type: OrderType;
  qty: number;
  filled_qty: number;
  limit_price: number | null;
  avg_fill_price: number | null;
  status: OrderStatus;
  strategy?: { id: string; name: string } | null;
};

export interface TradingOrdersResponse {
  items: TradingOrder[];
  next_cursor: string | null;
};

export type TradingOrderDetail = {
  order_id: string;
  symbol: string;
  side: OrderSide;
  type: OrderType;
  time_in_force: "day" | "gtc" | "ioc" | "fok";
  qty: number;
  filled_qty: number;
  limit_price: number | null;
  avg_fill_price: number | null;
  status: OrderStatus;
  submitted_at: string;
  filled_at: string | null;
  expires_at: string | null;
  source: "strategy" | "manual" | "api";
  strategy?: { id: string; name: string } | null;
};

export type TradingPositionItem = {
  symbol: string;
  qty: number;
  avg_price: number;
  market_price: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  strategy?: { id: string; name: string } | null;
};

export type TradingPositionsResponse = {
  items: TradingPositionItem[];
  as_of: string;
};

export interface OrderBook {
  bids: OrderBookLevel[];
  asks: OrderBookLevel[];
}

export interface RecentTrade {
  time: string;
  price: number;
  size: number;
  side: OrderSide;
}

export interface OpenOrder {
  id: string;
  symbol: string;
  side: OrderSide;
  type: OrderType;
  qty: number;
  filled: number;
  price: number;
  status: OrderStatus;
  strategy: string;
}
