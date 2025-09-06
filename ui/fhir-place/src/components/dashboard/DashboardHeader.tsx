import { Button } from "@/components/ui/button";
import { Clock, RefreshCw } from "lucide-react";

interface DashboardHeaderProps {
  autoRefresh: boolean;
  isRefreshing: boolean;
  onToggleAutoRefresh: () => void;
  onRefresh: () => void;
}

export function DashboardHeader({
  autoRefresh,
  isRefreshing,
  onToggleAutoRefresh,
  onRefresh,
}: DashboardHeaderProps) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Welcome back</h2>
        <p className="text-muted-foreground">
          Here&apos;s what&apos;s happening with your FHIR data today.
        </p>
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onToggleAutoRefresh}
          className={autoRefresh ? "bg-green-500/10 border-green-500/20" : ""}
        >
          <Clock className="h-4 w-4 mr-2" />
          Auto-refresh {autoRefresh ? "ON" : "OFF"}
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          disabled={isRefreshing}
          className="min-w-[100px]"
        >
          <RefreshCw
            className={`h-4 w-4 mr-2 ${isRefreshing ? "animate-spin" : ""}`}
          />
          {isRefreshing ? "Refreshing..." : "Refresh"}
        </Button>
      </div>
    </div>
  );
}
