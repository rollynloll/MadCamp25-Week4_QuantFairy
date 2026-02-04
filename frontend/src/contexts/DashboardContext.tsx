import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { getDashboard } from "@/api/dashboard";
import type { DashboardResponse, Range } from "@/types/dashboard";

interface DashboardState {
  data: DashboardResponse | null;
  loading: boolean;
  error: string | null;
  range: Range;
  setRange: (range: Range) => void;
  refresh: () => void;
}

const DashboardContext = createContext<DashboardState | null>(null);

export function DashboardProvider({ children }: { children: React.ReactNode }) {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [range, setRange] = useState<Range>("1M");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await getDashboard(range);
        if (isMounted) {
          setData(result);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load dashboard");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    load();

    return () => {
      isMounted = false;
    };
  }, [range, refreshKey]);

  const value = useMemo(
    () => ({
      data,
      loading,
      error,
      range,
      setRange,
      refresh: () => setRefreshKey((prev) => prev + 1),
    }),
    [data, loading, error, range]
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
