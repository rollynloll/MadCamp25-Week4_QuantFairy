import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import { getDashboard } from "@/api/dashboard";
import { getUserStrategies } from "@/api/userStrategies";
import type { DashboardResponse, Range } from "@/types/dashboard";
import type { UserStrategyListItem } from "@/types/portfolio";

interface DashboardState {
  data: DashboardResponse | null;
  loading: boolean;
  performanceLoading: boolean;
  error: string | null;
  userStrategies: UserStrategyListItem[] | null;
  userStrategiesLoading: boolean;
  refreshUserStrategies: () => void;
  range: Range;
  setRange: (range: Range) => void;
  refresh: () => void;
}

const DashboardContext = createContext<DashboardState | null>(null);

export function DashboardProvider({ children }: { children: React.ReactNode }) {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [performanceLoading, setPerformanceLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userStrategies, setUserStrategies] = useState<UserStrategyListItem[] | null>(null);
  const [userStrategiesLoading, setUserStrategiesLoading] = useState(false);
  const [userStrategiesRefreshKey, setUserStrategiesRefreshKey] = useState(0);
  const [range, setRange] = useState<Range>("1M");
  const [refreshKey, setRefreshKey] = useState(0);
  const initialLoadRef = useRef(true);

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      const isInitial = initialLoadRef.current;
      if (isInitial) {
        setLoading(true);
      } else {
        setPerformanceLoading(true);
      }
      setError(null);
      try {
        const result = await getDashboard(range);
        if (isMounted) {
          setData(result);
          initialLoadRef.current = false;
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load dashboard");
        }
      } finally {
        if (isMounted) {
          if (isInitial) {
            setLoading(false);
          } else {
            setPerformanceLoading(false);
          }
        }
      }
    };

    load();

    return () => {
      isMounted = false;
    };
  }, [range, refreshKey]);

  useEffect(() => {
    let isMounted = true;
    const env = data?.mode.environment ?? "paper";
    setUserStrategiesLoading(true);
    getUserStrategies(env)
      .then((result) => {
        if (isMounted) {
          setUserStrategies(result.items);
        }
      })
      .finally(() => {
        if (isMounted) {
          setUserStrategiesLoading(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, [data?.mode.environment, userStrategiesRefreshKey]);

  const value = useMemo(
    () => ({
      data,
      loading,
      performanceLoading,
      error,
      userStrategies,
      userStrategiesLoading,
      refreshUserStrategies: () => setUserStrategiesRefreshKey((prev) => prev + 1),
      range,
      setRange,
      refresh: () => setRefreshKey((prev) => prev + 1),
    }),
    [
      data,
      loading,
      performanceLoading,
      error,
      userStrategies,
      userStrategiesLoading,
      range,
    ]
  );

  return (
    <DashboardContext.Provider value={value}>
      {children}
    </DashboardContext.Provider>
  );
}

export function useDashboardContext() {
  const ctx = useContext(DashboardContext);
  if (!ctx) {
    throw new Error("useDashboardContext must be used within DashboardProvider");
  }
  return ctx;
}
