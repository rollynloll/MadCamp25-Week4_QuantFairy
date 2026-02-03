import type { OpenOrder, OrderBook, RecentTrade } from "@/types/trading";

export const orderBook: OrderBook = {
  bids: [
    { price: 178.24, size: 500, total: 89120 },
    { price: 178.23, size: 750, total: 133672.5 },
    { price: 178.22, size: 1200, total: 213864 },
    { price: 178.21, size: 850, total: 151478.5 },
    { price: 178.2, size: 2100, total: 374220 },
  ],
  asks: [
    { price: 178.25, size: 450, total: 80212.5 },
    { price: 178.26, size: 920, total: 163999.2 },
    { price: 178.27, size: 680, total: 121223.6 },
    { price: 178.28, size: 1500, total: 267420 },
    { price: 178.29, size: 750, total: 133717.5 },
  ],
};

export const recentTrades: RecentTrade[] = [
  { time: "14:32:15.234", price: 178.25, size: 100, side: "buy" },
  { time: "14:32:14.891", price: 178.24, size: 250, side: "sell" },
  { time: "14:32:13.567", price: 178.25, size: 75, side: "buy" },
  { time: "14:32:12.123", price: 178.26, size: 150, side: "buy" },
  { time: "14:32:10.456", price: 178.24, size: 200, side: "sell" },
  { time: "14:32:09.789", price: 178.23, size: 500, side: "sell" },
  { time: "14:32:08.234", price: 178.25, size: 350, side: "buy" },
  { time: "14:32:06.891", price: 178.24, size: 125, side: "sell" },
];

export const positions = [
  {
    symbol: "AAPL",
    qty: 250,
    side: "LONG",
    entryPrice: 176.85,
    currentPrice: 178.25,
    marketValue: 44562.5,
    unrealizedPnL: 350.0,
    unrealizedPnLPercent: 0.79,
    strategy: "Momentum Breakout",
  },
  {
    symbol: "MSFT",
    qty: -75,
    side: "SHORT",
    entryPrice: 414.20,
    currentPrice: 413.10,
    marketValue: -30982.5,
    unrealizedPnL: 82.5,
    unrealizedPnLPercent: 0.27,
    strategy: "Mean Reversion",
  },
  {
    symbol: "GOOGL",
    qty: 150,
    side: "LONG",
    entryPrice: 142.30,
    currentPrice: 143.75,
    marketValue: 21562.5,
    unrealizedPnL: 217.5,
    unrealizedPnLPercent: 1.02,
    strategy: "Pairs Trading",
  },
  {
    symbol: "TSLA",
    qty: 100,
    side: "LONG",
    entryPrice: 248.50,
    currentPrice: 245.20,
    marketValue: 24520.0,
    unrealizedPnL: -330.0,
    unrealizedPnLPercent: -1.33,
    strategy: "Statistical Arb",
  },
];