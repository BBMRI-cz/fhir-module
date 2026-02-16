"use client";

import { useState, useEffect, useCallback } from "react";
import { queryPrometheusAction } from "@/actions/prometheus/query";
import { fhirLastSyncQuery, fhirUpQuery } from "@/actions/prometheus/queries";

export type FetchState = "loading" | "loaded" | "error";

export interface SystemStatus {
  isOnline: boolean;
  lastChecked: string | null;
  lastSync: string | null;
  fetchState: FetchState;
  error: string | null;
}

export interface UseSystemStatusReturn {
  systemStatus: SystemStatus;
  isRefreshing: boolean;
  autoRefresh: boolean;
  setAutoRefresh: (value: boolean) => void;
  refresh: () => Promise<void>;
}

const parseTimestamp = (timestamp: number): string => {
  return new Date(timestamp * 1000).toLocaleString();
};

const parseLastSyncTimestamp = (timestampStr: string): string => {
  return new Date(parseInt(timestampStr)).toLocaleString();
};

export function useSystemStatus(): UseSystemStatusReturn {
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    isOnline: false,
    lastChecked: null,
    lastSync: null,
    fetchState: "loading",
    error: null,
  });

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchSystemStatus = useCallback(async () => {
    setSystemStatus((prev) => ({
      ...prev,
      fetchState: "loading",
      error: null,
    }));

    try {
      const [fhirModuleStatus, lastSyncTimestamp] = await Promise.all([
        queryPrometheusAction(fhirUpQuery),
        queryPrometheusAction(fhirLastSyncQuery),
      ]);

      const isOnline =
        fhirModuleStatus.success &&
        fhirModuleStatus.data?.result?.[0]?.value?.[1] === "1";

      const lastChecked =
        fhirModuleStatus.success &&
        fhirModuleStatus.data?.result?.[0]?.value?.[0]
          ? parseTimestamp(fhirModuleStatus.data.result[0].value[0])
          : null;

      const lastSync =
        lastSyncTimestamp.success &&
        lastSyncTimestamp.data?.result?.[0]?.value?.[1]
          ? parseLastSyncTimestamp(lastSyncTimestamp.data.result[0].value[1])
          : null;

      setSystemStatus({
        isOnline,
        lastChecked,
        lastSync,
        fetchState: "loaded",
        error: null,
      });
    } catch (error) {
      console.error("Error fetching system status:", error);
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error occurred";

      setSystemStatus((prev) => ({
        ...prev,
        fetchState: "error",
        error: errorMessage,
      }));
    }
  }, []);

  const refresh = async () => {
    setIsRefreshing(true);
    await fetchSystemStatus();
    setIsRefreshing(false);
  };

  useEffect(() => {
    fetchSystemStatus();
  }, [fetchSystemStatus]);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchSystemStatus, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchSystemStatus]);

  return {
    systemStatus,
    isRefreshing,
    autoRefresh,
    setAutoRefresh,
    refresh,
  };
}
