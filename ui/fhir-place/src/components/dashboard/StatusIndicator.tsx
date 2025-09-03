import { Badge } from "@/components/ui/badge";
import { AlertCircle, CheckCircle, Clock, Loader2 } from "lucide-react";
import { FetchState } from "@/hooks/useSystemStatus";

interface StatusIndicatorProps {
  fetchState: FetchState;
  isOnline?: boolean;
  label: string;
  hasData?: boolean;
}

const getStatusIcon = (fetchState: FetchState, isOnline?: boolean) => {
  if (fetchState === "loading") {
    return <Loader2 className="h-4 w-4 animate-spin text-blue-400" />;
  }

  if (fetchState === "error") {
    return <AlertCircle className="h-4 w-4 text-red-400" />;
  }

  if (isOnline !== undefined) {
    return isOnline ? (
      <CheckCircle className="h-4 w-4 text-green-400" />
    ) : (
      <AlertCircle className="h-4 w-4 text-red-400" />
    );
  }

  return <Clock className="h-4 w-4 text-green-400" />;
};

const getStatusBadge = (
  fetchState: FetchState,
  isOnline?: boolean,
  hasData?: boolean
) => {
  if (fetchState === "loading") {
    return {
      text: isOnline !== undefined ? "Checking..." : "Syncing...",
      className: "text-blue-400 border-blue-400",
    };
  }

  if (fetchState === "error") {
    return {
      text: "Error",
      className: "text-red-400 border-red-400",
    };
  }

  if (isOnline !== undefined) {
    return {
      text: isOnline ? "Online" : "Offline",
      className: isOnline
        ? "text-green-400 border-green-400"
        : "text-red-400 border-red-400",
    };
  }

  return {
    text: hasData ? "Success" : "No sync",
    className: hasData
      ? "text-green-400 border-green-400"
      : "text-gray-400 border-gray-400",
  };
};

export function StatusIndicator({
  fetchState,
  isOnline,
  label,
  hasData,
}: StatusIndicatorProps) {
  const icon = getStatusIcon(fetchState, isOnline);
  const badge = getStatusBadge(fetchState, isOnline, hasData);

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-md">{label}</span>
      </div>
      <Badge variant="outline" className={badge.className}>
        {badge.text}
      </Badge>
    </div>
  );
}
