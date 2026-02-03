import { useEffect, useRef, useState } from "react";
import type { OrderBook, OrderBookLevel, RecentTrade } from "@/types/trading";
import { API_BASE_URL } from "@/api/base";

export interface BarPoint {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface StreamMessage {
  type: "quote" | "trade" | "bar" | "status";
  symbol?: string;
  bid?: number;
  bid_size?: number;
  ask?: number;
  ask_size?: number;
  price?: number;
  size?: number;
  time?: string;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  volume?: number;
  message?: string;
}

const makeWsUrl = (path: string) => {
  const base = API_BASE_URL || window.location.origin;
  const wsBase = base.replace(/^http/, "ws");
  return `${wsBase}${path}`;
};

const initialBook: OrderBook = { bids: [], asks: [] };

export function useMarketStream(symbol: string) {
  const [orderBook, setOrderBook] = useState<OrderBook>(initialBook);
  const [trades, setTrades] = useState<RecentTrade[]>([]);
  const [bars, setBars] = useState<BarPoint[]>([]);
  const [status, setStatus] = useState<string>("connecting");
  const lastTradeRef = useRef<number | null>(null);

  useEffect(() => {
    if (!symbol) return;
    setStatus("connecting");
    const url = makeWsUrl(`/api/v1/trading/stream?symbols=${symbol}&channels=trades,quotes,bars`);
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setStatus("open");
      setOrderBook(initialBook);
      setTrades([]);
      setBars([]);
      lastTradeRef.current = null;
    };

    ws.onclose = () => setStatus("closed");
    ws.onerror = () => setStatus("error");

    ws.onmessage = (event) => {
      let msg: StreamMessage | null = null;
      try {
        msg = JSON.parse(event.data) as StreamMessage;
      } catch {
        return;
      }
      if (!msg || msg.type === "status") return;

      if (msg.type === "quote") {
        const bid = Number(msg.bid ?? 0);
        const ask = Number(msg.ask ?? 0);
        const bidSize = Number(msg.bid_size ?? 0);
        const askSize = Number(msg.ask_size ?? 0);
        setOrderBook((prev) => {
          const makeLevel = (price: number, size: number): OrderBookLevel => ({
            price,
            size,
            total: price * size,
          });
          const nextAsks = ask ? [makeLevel(ask, askSize), ...prev.asks].slice(0, 5) : prev.asks;
          const nextBids = bid ? [makeLevel(bid, bidSize), ...prev.bids].slice(0, 5) : prev.bids;
          return { asks: nextAsks, bids: nextBids };
        });
        return;
      }

      if (msg.type === "trade") {
        const price = Number(msg.price ?? 0);
        const size = Number(msg.size ?? 0);
        const previous = lastTradeRef.current;
        const side: "buy" | "sell" = previous !== null && price < previous ? "sell" : "buy";
        lastTradeRef.current = price;
        setTrades((prev) => {
          const next: RecentTrade[] = [
            {
              time: msg.time ?? new Date().toISOString(),
              price,
              size,
              side,
            },
            ...prev,
          ];
          return next.slice(0, 40);
        });
        return;
      }

      if (msg.type === "bar") {
        const point: BarPoint = {
          time: msg.time ?? new Date().toISOString(),
          open: Number(msg.open ?? 0),
          high: Number(msg.high ?? 0),
          low: Number(msg.low ?? 0),
          close: Number(msg.close ?? 0),
          volume: Number(msg.volume ?? 0),
        };
        setBars((prev) => {
          const next = [...prev];
          const last = next[next.length - 1];
          if (last && last.time === point.time) {
            next[next.length - 1] = point;
          } else {
            next.push(point);
          }
          return next.slice(-120);
        });
      }
    };

    return () => {
      ws.close();
    };
  }, [symbol]);

  const midPrice = (() => {
    const bid = orderBook.bids[0]?.price;
    const ask = orderBook.asks[0]?.price;
    if (bid && ask) return (bid + ask) / 2;
    return bid || ask || lastTradeRef.current || 0;
  })();

  const spread = (() => {
    const bid = orderBook.bids[0]?.price;
    const ask = orderBook.asks[0]?.price;
    if (bid && ask) return Math.max(ask - bid, 0);
    return 0;
  })();

  return {
    orderBook,
    trades,
    bars,
    midPrice,
    spread,
    status,
  };
}
