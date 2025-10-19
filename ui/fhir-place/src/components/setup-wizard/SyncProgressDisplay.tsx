import {
  RefreshCw,
  Database,
  Building2,
  Users,
  FileText,
  TestTube,
} from "lucide-react";
import { Progress } from "@/components/ui/progress";
import {
  getSyncProgress,
  getMiabisSyncProgress,
  type SyncProgressResponse,
} from "@/actions/backend/sync-progress";
import {
  useState,
  useEffect,
  useCallback,
  forwardRef,
  useImperativeHandle,
} from "react";

const RESOURCE_ICONS = {
  organizations: Building2,
  patients: Users,
  conditions: FileText,
  specimens: TestTube,
  biobank: Building2,
  collections: Building2,
} as const;

const RESOURCE_LABELS = {
  biobank: "Biobank",
  collections: "Collections",
  organizations: "Organizations",
  patients: "Patients",
  conditions: "Conditions",
  specimens: "Specimens",
} as const;

const PHASE_NAMES = [
  "Idle",
  "Organizations",
  "Patients",
  "Conditions",
  "Specimens",
] as const;

const RESOURCE_ORDER = [
  "organizations",
  "biobank",
  "collections",
  "patients",
  "conditions",
  "specimens",
] as const;

export interface SyncProgressDisplayHandle {
  start: (isMiabisMode: boolean) => void;
  stop: () => void;
  reset: () => void;
}

interface SyncProgressDisplayProps {
  onComplete?: () => void;
}

const SyncProgressDisplay = forwardRef<
  SyncProgressDisplayHandle,
  SyncProgressDisplayProps
>(({ onComplete }, ref) => {
  const [syncProgress, setSyncProgress] = useState<SyncProgressResponse | null>(
    null
  );
  const [isPolling, setIsPolling] = useState(false);
  const [isCompleting, setIsCompleting] = useState(false);
  const [shouldRender, setShouldRender] = useState(false);
  const [currentIsMiabisMode, setCurrentIsMiabisMode] = useState(false);

  const fetchProgress = useCallback(async () => {
    try {
      const progress = currentIsMiabisMode
        ? await getMiabisSyncProgress()
        : await getSyncProgress();
      setSyncProgress(progress);

      if (!progress.in_progress) {
        setIsPolling(false);
        setIsCompleting(true);

        setTimeout(() => {
          setShouldRender(false);
          setIsCompleting(false);
          if (onComplete) {
            onComplete();
          }
        }, 2000);
      }
    } catch (error) {
      console.error("Error fetching sync progress:", error);
      setIsPolling(false);
    }
  }, [onComplete, currentIsMiabisMode]);

  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;

    if (isPolling) {
      fetchProgress();

      intervalId = setInterval(fetchProgress, 1000);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [isPolling, fetchProgress]);

  useImperativeHandle(
    ref,
    () => ({
      start: (isMiabisMode: boolean) => {
        setCurrentIsMiabisMode(isMiabisMode);
        setSyncProgress(null);
        setIsCompleting(false);
        setShouldRender(true);

        setTimeout(() => {
          const initialResources: Record<
            string,
            { current: number; total: number; percentage: number }
          > = isMiabisMode
            ? {
                biobank: { current: 0, total: 0, percentage: 0 },
                collections: { current: 0, total: 0, percentage: 0 },
                patients: { current: 0, total: 0, percentage: 0 },
                specimens: { current: 0, total: 0, percentage: 0 },
              }
            : {
                organizations: { current: 0, total: 0, percentage: 0 },
                patients: { current: 0, total: 0, percentage: 0 },
                conditions: { current: 0, total: 0, percentage: 0 },
                specimens: { current: 0, total: 0, percentage: 0 },
              };

          setSyncProgress({
            in_progress: true,
            current_phase: 0,
            resources: initialResources,
          });

          setIsPolling(true);
        }, 100);
      },
      stop: () => {
        setIsPolling(false);
      },
      reset: () => {
        setCurrentIsMiabisMode(false);
        setSyncProgress(null);
        setIsPolling(false);
        setIsCompleting(false);
        setShouldRender(false);
      },
    }),
    []
  );

  if (!shouldRender) {
    return null;
  }

  return (
    <div
      className={`space-y-4 pt-4 transition-opacity duration-[2000ms] ${
        isCompleting ? "opacity-0" : "opacity-100"
      }`}
    >
      <div className="flex items-center justify-center space-x-2">
        <RefreshCw
          className={`w-4 h-4 ${isCompleting ? "" : "animate-spin"}`}
        />
        <span className="text-sm font-medium">
          Syncing - Phase: {PHASE_NAMES[syncProgress?.current_phase || 0]}
        </span>
      </div>

      <div className="space-y-3">
        {RESOURCE_ORDER.map((resourceType) => {
          const data = syncProgress?.resources[resourceType];
          if (!data) return null;

          const Icon = RESOURCE_ICONS[resourceType] || Database;
          const label = RESOURCE_LABELS[resourceType] || resourceType;

          return (
            <div
              key={resourceType}
              className="space-y-2 p-3 bg-muted/50 rounded-lg"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Icon className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium">{label}</span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {data.current} / {data.total}
                </span>
              </div>
              <div className="space-y-1">
                <Progress value={data.percentage} className="h-2" />
                <div className="text-xs text-right text-muted-foreground">
                  {data.percentage.toFixed(1)}%
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
});

SyncProgressDisplay.displayName = "SyncProgressDisplay";

export default SyncProgressDisplay;
