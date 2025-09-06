import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SystemStatus } from "@/hooks/useSystemStatus";
import { StatusIndicator } from "./StatusIndicator";

interface SystemHealthCardProps {
  systemStatus: SystemStatus;
}

export function SystemHealthCard({ systemStatus }: SystemHealthCardProps) {
  const getLastCheckedText = () => {
    if (systemStatus.fetchState === "loading") {
      return "Checking now...";
    }
    return systemStatus.lastChecked || "Never";
  };

  return (
    <Card className="border-2">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div>
          <CardTitle className="text-3xl font-medium">System Health</CardTitle>
          <div className="text-base font-medium text-foreground/90 mt-2">
            Last checked:{" "}
            <span className="font-normal">{getLastCheckedText()}</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <StatusIndicator
          fetchState={systemStatus.fetchState}
          isOnline={systemStatus.isOnline}
          label="FHIR Module"
        />
        <StatusIndicator
          fetchState={systemStatus.fetchState}
          label="Last Sync"
          hasData={!!systemStatus.lastSync}
        />
      </CardContent>
    </Card>
  );
}
