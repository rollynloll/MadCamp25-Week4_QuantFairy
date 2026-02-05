import { useEffect, useRef, useState } from "react";
import type { OrderBook, OrderBookLevel, RecentTrade } from "@/types/trading";
import { API_BASE_URL } from "@/api/base";
import { getTradingBars, getTradingQuote } from "@/api/trading";

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
  const normalizedBase = base.replace(/\/api\/v1\/?$/, "");
  const normalizedPath = path.startsWith("/api/v1")
    ? path
    : `/api/v1${path.startsWith("/") ? "" : "/"}${path}`;
  const wsBase = normalizedBase.replace(/^http/, "ws");
  return `${wsBase}${normalizedPath}`;
};

const initialBook: OrderBook = { bids: [], asks: [] };

export type MarketTimeframe = "1D" | "1W" | "1M" | "3M" | "1Y";

const resolveHistoryParams = (timeframe: MarketTimeframe) => {
  switch (timeframe) {
    case "1W":
      return { timeframe: "1Hour", limit: 168 };
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
    const t = parseTimeMs(bar.time);
    return Number.isNaN(t) ? true : t >= cutoff;
  });
  return filtered.length ? filtered : bars;
};

const parseTimeMs = (value: string) => {
  let t = new Date(value).getTime();
  if (!Number.isNaN(t)) return t;
  if (value.includes(" ")) {
    t = new Date(value.replace(" ", "T")).getTime();
    if (!Number.isNaN(t)) return t;
  }
  if (!value.endsWith("Z")) {
    t = new Date(`${value}Z`).getTime();
  }
  return t;
};

const aggregateDaily = (bars: BarPoint[]) => {
  if (!bars.length) return bars;
  const groups = new Map<string, BarPoint[]>();
  for (const bar of bars) {
    const ms = parseTimeMs(bar.time);
    if (Number.isNaN(ms)) continue;
    const dayKey = new Date(ms).toISOString().slice(0, 10);
    if (!groups.has(dayKey)) {
      groups.set(dayKey, []);
    }
    groups.get(dayKey)!.push(bar);
  }
  const daily: BarPoint[] = [];
  Array.from(groups.entries())
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
    .forEach(([day, items]) => {
      items.sort((a, b) => parseTimeMs(a.time) - parseTimeMs(b.time));
      const open = items[0].open;
      const close = items[items.length - 1].close;
      const high = Math.max(...items.map((i) => i.high));
      const low = Math.min(...items.map((i) => i.low));
      const volume = items.reduce((sum, i) => sum + (i.volume || 0), 0);
      daily.push({
        time: `${day}T00:00:00Z`,
        open,
        high,
        low,
        close,
        volume,
      });
    });
  return daily;
};

export function useMarketStream(symbol: string, timeframe: MarketTimeframe = "1D") {
  const [orderBook, setOrderBook] = useState<OrderBook>(initialBook);
  const [trades, setTrades] = useState<RecentTrade[]>([]);
  const [bars, setBars] = useState<BarPoint[]>([]);
  const [status, setStatus] = useState<string>("connecting");
  const lastTradeRef = useRef<number | null>(null);
  const hasStreamedBars = useRef(false);
  const timeframeRef = useRef<MarketTimeframe>(timeframe);
  const lastQuoteUpdateMsRef = useRef<number>(0);
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
        lastQuoteUpdateMsRef.current = Date.now();
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
        const tradeTime = msg.time ?? new Date().toISOString();
        const previous = lastTradeRef.current;
        const side: "buy" | "sell" = previous !== null && price < previous ? "sell" : "buy";
        lastTradeRef.current = price;
        setTrades((prev) => {
          const next: RecentTrade[] = [
            {
              time: tradeTime,
              price,
              size,
              side,
            },
            ...prev,
          ];
          return next.slice(0, 40);
        });
        if (timeframeRef.current === "1D" && Number.isFinite(price) && price > 0) {
          setBars((prev) => {
            const next = [...prev];
            if (!next.length) {
              return [
                {
                  time: tradeTime,
                  open: price,
                  high: price,
                  low: price,
                  close: price,
                  volume: Number.isFinite(size) ? size : 0,
                },
              ];
            }

            const last = next[next.length - 1];
            const tradeMs = parseTimeMs(tradeTime);
            const lastMs = parseTimeMs(last.time);
            const sameMinute =
              !Number.isNaN(tradeMs) &&
              !Number.isNaN(lastMs) &&
              Math.floor(tradeMs / 60000) === Math.floor(lastMs / 60000);

            if (sameMinute) {
              next[next.length - 1] = {
                ...last,
                high: Math.max(last.high, price),
                low: Math.min(last.low, price),
                close: price,
                volume: (last.volume || 0) + (Number.isFinite(size) ? size : 0),
              };
            } else {
              const baseOpen = Number.isFinite(last.close) ? last.close : price;
              next.push({
                time: tradeTime,
                open: baseOpen,
                high: Math.max(baseOpen, price),
                low: Math.min(baseOpen, price),
                close: price,
                volume: Number.isFinite(size) ? size : 0,
              });
            }

            return next.slice(-600);
          });
        }
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

    const applyQuote = async () => {
      try {
        const quote = await getTradingQuote({ symbol, feed });
        if (cancelled) return;
        const bid = Number(quote.bid ?? 0);
        const ask = Number(quote.ask ?? 0);
        const bidSize = Number(quote.bid_size ?? 0);
        const askSize = Number(quote.ask_size ?? 0);
        if (bid <= 0 && ask <= 0) return;

        const makeLevel = (price: number, size: number): OrderBookLevel => ({
          price,
          size: Number.isFinite(size) && size > 0 ? size : 1,
          total: price * (Number.isFinite(size) && size > 0 ? size : 1),
        });
        let applied = false;
        setOrderBook((prev) => {
          const shouldOverrideFromRest =
            prev.bids.length === 0 ||
            prev.asks.length === 0 ||
            Date.now() - lastQuoteUpdateMsRef.current > 12_000;
          if (!shouldOverrideFromRest) {
            return prev;
          }
          applied = true;
          return {
            bids: bid > 0 ? [makeLevel(bid, bidSize)] : [],
            asks: ask > 0 ? [makeLevel(ask, askSize)] : [],
          };
        });
        if (applied) {
          lastQuoteUpdateMsRef.current = Date.now();
          const fallbackMid = quote.mid ?? (bid > 0 && ask > 0 ? (bid + ask) / 2 : bid || ask);
          if (fallbackMid && fallbackMid > 0) {
            lastTradeRef.current = fallbackMid;
          }
        }
      } catch {
        // ignore quote polling failures; websocket/historical data may still work
      }
    };

    void applyQuote();
    const timer = window.setInterval(() => {
      void applyQuote();
    }, 5000);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [symbol, feed]);

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
        if (!res.bars?.length || res.bars.length < 2) {
          if (timeframe === "1D") {
            res = await getTradingBars({ symbol, timeframe: "1Min", limit: 390, feed });
          } else {
            res = await getTradingBars({ symbol, timeframe: "1Day", limit: 365, feed });
          }
          if (cancelled) return;
          if (hasStreamedBars.current) return;
        }
        if (!res.bars?.length || res.bars.length < 2) {
          if (timeframe === "1D") {
            res = await getTradingBars({ symbol, timeframe: "1Min", limit: 120, feed });
          } else {
            res = await getTradingBars({ symbol, timeframe: "1Hour", limit: 1000, feed });
          }
          if (cancelled) return;
          if (hasStreamedBars.current) return;
        }
        if (!res.bars?.length) return;
        const history = res.bars
          .map((bar) => ({
            time: bar.time,
            open: Number(bar.open ?? 0),
            high: Number(bar.high ?? 0),
            low: Number(bar.low ?? 0),
            close: Number(bar.close ?? 0),
            volume: Number(bar.volume ?? 0),
          }))
          .filter(
            (bar) =>
              Number.isFinite(bar.open) &&
              Number.isFinite(bar.high) &&
              Number.isFinite(bar.low) &&
              Number.isFinite(bar.close) &&
              !Number.isNaN(parseTimeMs(bar.time))
          )
          .sort((a, b) => parseTimeMs(a.time) - parseTimeMs(b.time));
        const windowed = applyTimeWindow(history, timeframe);
        if (timeframe === "1D" || timeframe === "1W") {
          setBars(windowed);
        } else {
          setBars(aggregateDaily(windowed));
        }
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
