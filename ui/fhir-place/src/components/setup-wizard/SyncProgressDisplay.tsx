import {
  RefreshCw,
  Database,
  Building2,
  Users,
  FileText,
  TestTube,
  Check,
  Clock,
  Loader2,
} from "lucide-react";
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
  useRef,
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

const RESOURCE_PHASE: Record<string, number> = {
  organizations: 1,
  biobank: 1,
  collections: 1,
  patients: 2,
  conditions: 3,
  specimens: 4,
};

type SyncStatus = "pending" | "in_progress" | "completed";

function getResourceStatus(
  resourceType: string,
  currentPhase: number,
  isCompleting: boolean
): SyncStatus {
  const resourcePhase = RESOURCE_PHASE[resourceType] || 0;

  if (isCompleting) {
    return "completed";
  }

  if (currentPhase > resourcePhase) {
    return "completed";
  } else if (currentPhase === resourcePhase) {
    return "in_progress";
  }
  return "pending";
}

interface SyncState {
  progress: SyncProgressResponse | null;
  isPolling: boolean;
  isCompleting: boolean;
  shouldRender: boolean;
}

const initialSyncState: SyncState = {
  progress: null,
  isPolling: false,
  isCompleting: false,
  shouldRender: false,
};

const isIdleProgress = (progress: SyncProgressResponse) => {
  if (!progress.in_progress) return true;

  const hasWork = Object.values(progress.resources || {}).some(
    (res) => (res?.current ?? 0) > 0
  );

  return !hasWork;
};

export interface SyncRunningStatus {
  blazeSyncRunning: boolean;
  miabisSyncRunning: boolean;
}

export interface SyncProgressDisplayHandle {
  start: (isMiabisMode: boolean) => void;
  stop: () => void;
  reset: () => void;
}

interface SyncProgressDisplayProps {
  onComplete?: () => void;
  onSyncStatusChange?: (status: SyncRunningStatus) => void;
}

interface SingleSyncProgressProps {
  title: string;
  progress: SyncProgressResponse | null;
  isCompleting: boolean;
}

function SingleSyncProgress({
  title,
  progress,
  isCompleting,
}: SingleSyncProgressProps) {
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
          {title} - Phase: {PHASE_NAMES[progress?.current_phase || 0]}
        </span>
      </div>

      <div className="space-y-3">
        {RESOURCE_ORDER.map((resourceType) => {
          const data = progress?.resources[resourceType];
          if (!data) return null;

          const Icon = RESOURCE_ICONS[resourceType] || Database;
          const label = RESOURCE_LABELS[resourceType] || resourceType;
          const status = getResourceStatus(
            resourceType,
            progress?.current_phase || 0,
            isCompleting
          );

          const statusStyles = {
            pending: "bg-muted/30 text-muted-foreground",
            in_progress: "bg-blue-500/10 border border-blue-500/30",
            completed: "bg-green-500/10 border border-green-500/30",
          };

          const StatusIcon = {
            pending: Clock,
            in_progress: Loader2,
            completed: Check,
          }[status];

          return (
            <div
              key={resourceType}
              className={`flex items-center justify-between p-3 rounded-lg transition-all duration-300 ${statusStyles[status]}`}
            >
              <div className="flex items-center space-x-2">
                <Icon className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium">{label}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-semibold tabular-nums">
                  {data.current.toLocaleString()} processed
                </span>
                <StatusIcon
                  className={`w-4 h-4 ${
                    status === "completed"
                      ? "text-green-500"
                      : status === "in_progress"
                      ? "text-blue-500 animate-spin"
                      : "text-muted-foreground"
                  }`}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const SyncProgressDisplay = forwardRef<
  SyncProgressDisplayHandle,
  SyncProgressDisplayProps
>(({ onComplete, onSyncStatusChange }, ref) => {
  const [blazeState, setBlazeState] = useState<SyncState>(initialSyncState);
  const [miabisState, setMiabisState] = useState<SyncState>(initialSyncState);

  const onCompleteRef = useRef(onComplete);
  const onSyncStatusChangeRef = useRef(onSyncStatusChange);

  useEffect(() => {
    onCompleteRef.current = onComplete;
    onSyncStatusChangeRef.current = onSyncStatusChange;
  });

  useEffect(() => {
    onSyncStatusChangeRef.current?.({
      blazeSyncRunning: blazeState.shouldRender && !blazeState.isCompleting,
      miabisSyncRunning: miabisState.shouldRender && !miabisState.isCompleting,
    });
  }, [
    blazeState.shouldRender,
    blazeState.isCompleting,
    miabisState.shouldRender,
    miabisState.isCompleting,
  ]);

  const fetchBlazeProgress = useCallback(async () => {
    try {
      const progress = await getSyncProgress();

      setBlazeState((prev) => {
        if (!prev.shouldRender && isIdleProgress(progress)) {
          return initialSyncState;
        }
        return { ...prev, progress };
      });

      if (!progress.in_progress) {
        setBlazeState((prev) => ({
          ...prev,
          isPolling: false,
          isCompleting: true,
        }));

        setTimeout(() => {
          setBlazeState((prev) => ({
            ...prev,
            shouldRender: false,
            isCompleting: false,
          }));
          setMiabisState((current) => {
            if (!current.shouldRender) {
              onCompleteRef.current?.();
            }
            return current;
          });
        }, 2000);
      }
    } catch (error) {
      console.error("Error fetching blaze sync progress:", error);
      setBlazeState(() => ({
        ...initialSyncState,
      }));
    }
  }, []);

  const fetchMiabisProgress = useCallback(async () => {
    try {
      const progress = await getMiabisSyncProgress();

      setMiabisState((prev) => {
        if (!prev.shouldRender && isIdleProgress(progress)) {
          return initialSyncState;
        }
        return { ...prev, progress };
      });

      if (!progress.in_progress) {
        setMiabisState((prev) => ({
          ...prev,
          isPolling: false,
          isCompleting: true,
        }));

        setTimeout(() => {
          setMiabisState((prev) => ({
            ...prev,
            shouldRender: false,
            isCompleting: false,
          }));
          setBlazeState((current) => {
            if (!current.shouldRender) {
              onCompleteRef.current?.();
            }
            return current;
          });
        }, 2000);
      }
    } catch (error) {
      console.error("Error fetching miabis sync progress:", error);
      setMiabisState(() => ({
        ...initialSyncState,
      }));
    }
  }, []);

  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;

    if (blazeState.isPolling) {
      fetchBlazeProgress();
      intervalId = setInterval(fetchBlazeProgress, 1000);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [blazeState.isPolling, fetchBlazeProgress]);

  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;

    if (miabisState.isPolling) {
      fetchMiabisProgress();
      intervalId = setInterval(fetchMiabisProgress, 1000);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [miabisState.isPolling, fetchMiabisProgress]);

  useImperativeHandle(
    ref,
    () => ({
      start: (isMiabisMode: boolean) => {
        if (isMiabisMode) {
          setMiabisState({
            progress: null,
            isPolling: false,
            isCompleting: false,
            shouldRender: true,
          });

          setTimeout(() => {
            const initialResources: Record<string, { current: number }> = {
              biobank: { current: 0 },
              collections: { current: 0 },
              patients: { current: 0 },
              specimens: { current: 0 },
            };

            setMiabisState((prev) => ({
              ...prev,
              progress: {
                in_progress: true,
                current_phase: 0,
                resources: initialResources,
              },
              isPolling: true,
            }));
          }, 100);
        } else {
          setBlazeState({
            progress: null,
            isPolling: false,
            isCompleting: false,
            shouldRender: true,
          });

          setTimeout(() => {
            const initialResources: Record<string, { current: number }> = {
              organizations: { current: 0 },
              patients: { current: 0 },
              conditions: { current: 0 },
              specimens: { current: 0 },
            };

            setBlazeState((prev) => ({
              ...prev,
              progress: {
                in_progress: true,
                current_phase: 0,
                resources: initialResources,
              },
              isPolling: true,
            }));
          }, 100);
        }
      },
      stop: () => {
        setBlazeState((prev) => ({ ...prev, isPolling: false }));
        setMiabisState((prev) => ({ ...prev, isPolling: false }));
      },
      reset: () => {
        setBlazeState(initialSyncState);
        setMiabisState(initialSyncState);
      },
    }),
    []
  );

  if (!blazeState.shouldRender && !miabisState.shouldRender) {
    return null;
  }

  return (
    <div className="space-y-6">
      {blazeState.shouldRender && (
        <SingleSyncProgress
          title="Syncing BLAZE"
          progress={blazeState.progress}
          isCompleting={blazeState.isCompleting}
        />
      )}
      {miabisState.shouldRender && (
        <SingleSyncProgress
          title="Syncing MIABIS"
          progress={miabisState.progress}
          isCompleting={miabisState.isCompleting}
        />
      )}
    </div>
  );
});

SyncProgressDisplay.displayName = "SyncProgressDisplay";

export default SyncProgressDisplay;
