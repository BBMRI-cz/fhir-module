"use client";

import { useState, useEffect } from "react";
import { checkBackendHealth } from "@/actions/backend/health-check";

export function useBackendStatus(pollInterval: number = 10000) {
  const [isBackendOnline, setIsBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    const checkStatus = async () => {
      const result = await checkBackendHealth();
      setIsBackendOnline(result.isHealthy);
    };

    checkStatus();

    const interval = setInterval(checkStatus, pollInterval);

    return () => clearInterval(interval);
  }, [pollInterval]);

  return isBackendOnline;
}
