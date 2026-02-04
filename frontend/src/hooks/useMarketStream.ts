import { useEffect, useRef, useState } from "react";
import type { OrderBook, OrderBookLevel, RecentTrade } from "@/types/trading";
import { API_BASE_URL } from "@/api/base";
import { getTradingBars } from "@/api/trading";

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

const resolveBaseUrl = () => {
  if (API_BASE_URL) return API_BASE_URL;
  if (window.location.hostname === "localhost" && window.location.port === "5173") {
    return "http://localhost:8000";
  }
  return window.location.origin;
};

const makeWsUrl = (path: string) => {
  const base = resolveBaseUrl();
  const wsBase = base.replace(/^http/, "ws");
  return `${wsBase}${path}`;
};

const initialBook: OrderBook = { bids: [], asks: [] };

export type MarketTimeframe = "1D" | "1W" | "1M" | "3M" | "1Y";

const resolveHistoryParams = (timeframe: MarketTimeframe) => {
  switch (timeframe) {
    case "1W":
      return { timeframe: "1Day", limit: 7 };
    case "1M":
      return { timeframe: "1Day", limit: 30 };
    case "3M":
      return { timeframe: "1Day", limit: 90 };
    case "1Y":
      return { timeframe: "1Day", limit: 365 };
    default:
      return { timeframe: "1Min", limit: 390 };
  }
};

const resolveWindowDays = (timeframe: MarketTimeframe) => {
  switch (timeframe) {
    case "1W":
      return 7;
    case "1M":
      return 30;
    case "3M":
      return 90;
    case "1Y":
      return 365;
    default:
      return 1;
  }
};

const applyTimeWindow = (bars: BarPoint[], timeframe: MarketTimeframe) => {
  if (!bars.length) return bars;
  const days = resolveWindowDays(timeframe);
  const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;
  const filtered = bars.filter((bar) => {
    const t = new Date(bar.time).getTime();
    return Number.isNaN(t) ? true : t >= cutoff;
  });
  return filtered.length ? filtered : bars;
};

export function useMarketStream(symbol: string, timeframe: MarketTimeframe = "1D") {
  const [orderBook, setOrderBook] = useState<OrderBook>(initialBook);
  const [trades, setTrades] = useState<RecentTrade[]>([]);
  const [bars, setBars] = useState<BarPoint[]>([]);
  const [status, setStatus] = useState<string>("connecting");
  const lastTradeRef = useRef<number | null>(null);
  const hasStreamedBars = useRef(false);
  const timeframeRef = useRef<MarketTimeframe>(timeframe);
  const feed = "iex";

  useEffect(() => {
    timeframeRef.current = timeframe;
  }, [timeframe]);

  useEffect(() => {
    if (!symbol) return;
    setStatus("connecting");
    setOrderBook(initialBook);
    setTrades([]);
    setBars([]);
    lastTradeRef.current = null;
    hasStreamedBars.current = false;
    const url = makeWsUrl(
      `/api/v1/trading/stream?symbols=${encodeURIComponent(
        symbol
      )}&channels=trades,quotes,bars&feed=${feed}`
    );
    const ws = new WebSocket(url);
    let shouldClose = false;

    ws.onopen = () => {
      if (shouldClose) {
        ws.close();
        return;
      }
      setStatus("open");
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
      if (!msg) return;
      if (msg.type === "status") {
        if (msg.message) {
          setStatus(msg.message);
        }
        return;
      }

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
        if (timeframeRef.current !== "1D") {
          return;
        }
        hasStreamedBars.current = true;
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
      if (ws.readyState === WebSocket.CONNECTING) {
        shouldClose = true;
      } else if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [symbol]);

  useEffect(() => {
    if (!symbol) return;
    let cancelled = false;
    setBars([]);
    hasStreamedBars.current = false;

    const loadHistory = async () => {
      try {
        const historyParams = resolveHistoryParams(timeframe);
        let res = await getTradingBars({
          symbol,
          timeframe: historyParams.timeframe,
          limit: historyParams.limit,
          feed,
        });
        if (cancelled) return;
        if (hasStreamedBars.current) return;
        if (
          timeframe === "1D" &&
          (!res.bars?.length || res.bars.length < 50)
        ) {
          res = await getTradingBars({ symbol, timeframe: "1Day", limit: 365, feed });
          if (cancelled) return;
          if (hasStreamedBars.current) return;
        }
        if (!res.bars?.length) return;
        const history = res.bars.map((bar) => ({
          time: bar.time,
          open: bar.open,
          high: bar.high,
          low: bar.low,
          close: bar.close,
          volume: bar.volume,
        }));
        setBars(applyTimeWindow(history, timeframe));
        lastTradeRef.current = history[history.length - 1]?.close ?? lastTradeRef.current;
      } catch {
        // ignore history fetch failures; stream may still work
      }
    };

    loadHistory();
    return () => {
      cancelled = true;
    };
  }, [symbol, timeframe]);

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
