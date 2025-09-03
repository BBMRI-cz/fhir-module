"use client";

import { useSystemStatus } from "@/hooks/useSystemStatus";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { SystemHealthCard } from "@/components/dashboard/SystemHealthCard";

export default function DashboardPage() {
  const { systemStatus, isRefreshing, autoRefresh, setAutoRefresh, refresh } =
    useSystemStatus();

  return (
    <main className="flex-1 p-6">
      <div className="space-y-6">
        <DashboardHeader
          autoRefresh={autoRefresh}
          isRefreshing={isRefreshing}
          onToggleAutoRefresh={() => setAutoRefresh(!autoRefresh)}
          onRefresh={refresh}
        />

        <div className="grid gap-4 grid-cols-2">
          <SystemHealthCard systemStatus={systemStatus} />
        </div>
      </div>
    </main>
  );
}
