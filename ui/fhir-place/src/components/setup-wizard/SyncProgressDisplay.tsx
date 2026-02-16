"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import {
  getMiabisSyncProgress,
  getSyncProgress,
  type SyncProgressResponse,
} from "@/actions/backend/sync-progress";
import { Badge } from "@/components/ui/badge";
import {
  Activity,
  RefreshCw,
  Building2,
  Users,
  FileText,
  TestTube,
  Layers,
  Database,
} from "lucide-react";
import { SyncTarget } from "@/types/setup-wizard/types";

type SyncType = "blaze" | "miabis";

interface SyncState {
  data: SyncProgressResponse | null;
  isVisible: boolean;
  isFadingOut: boolean;
}

interface SyncProgressDisplayProps {
  syncTargets?: SyncTarget[];
}

const SYNC_CONFIG: Record<
  SyncType,
  {
    label: string;
    fetcher: () => Promise<SyncProgressResponse>;
    accent: string;
    Icon: typeof Activity;
  }
> = {
  blaze: {
    label: "BLAZE Sync Progress",
    fetcher: getSyncProgress,
    accent: "text-blue-600",
    Icon: RefreshCw,
  },
  miabis: {
    label: "MIABIS Sync Progress",
    fetcher: getMiabisSyncProgress,
    accent: "text-purple-600",
    Icon: Activity,
  },
};

const RESOURCE_LABELS: Record<string, string> = {
  organizations: "Organizations",
  patients: "Patients",
  conditions: "Conditions",
  specimens: "Specimens",
  biobank: "Biobank",
  collections: "Collections",
};

const RESOURCE_ICONS: Record<string, typeof Activity> = {
  organizations: Building2,
  patients: Users,
  conditions: FileText,
  specimens: TestTube,
  collections: Layers,
};

const PHASE_LABELS: Record<number, string> = {
  0: "Idle",
  1: "Organizations",
  2: "Patients",
  3: "Conditions",
  4: "Specimens",
};

function formatResourceName(resourceType: string) {
  return (
    RESOURCE_LABELS[resourceType] ||
    `${resourceType.charAt(0).toUpperCase()}${resourceType.slice(1)}`
  );
}

function getResourceIcon(resourceType: string) {
  return RESOURCE_ICONS[resourceType] || Database;
}

function getPhaseLabel(phase?: number) {
  if (phase === undefined || phase === null) {
    return "Idle";
  }
  return PHASE_LABELS[phase] || `Phase ${phase}`;
}

export default function SyncProgressDisplay({
  syncTargets = [],
}: SyncProgressDisplayProps) {
  const [syncState, setSyncState] = useState<Record<SyncType, SyncState>>({
    blaze: { data: null, isVisible: false, isFadingOut: false },
    miabis: { data: null, isVisible: false, isFadingOut: false },
  });

  // Determine which sync types should be enabled based on syncTargets
  const enabledSyncTypes = useMemo(() => {
    const types: SyncType[] = [];
    if (syncTargets.includes("blaze") || syncTargets.includes("both")) {
      types.push("blaze");
    }
    if (syncTargets.includes("miabis") || syncTargets.includes("both")) {
      types.push("miabis");
    }
    return types;
  }, [syncTargets]);

  const anySyncRunningRef = useRef(false);

  useEffect(() => {
    // Don't poll if no sync types are enabled
    if (enabledSyncTypes.length === 0) {
      return;
    }

    let isMounted = true;
    let pollTimeout: NodeJS.Timeout | null = null;
    const fadeOutTimeouts: Record<SyncType, NodeJS.Timeout | null> = {
      blaze: null,
      miabis: null,
    };

    const POLL_INTERVAL = 1000;

    const fetchProgress = async () => {
      const fetchers = enabledSyncTypes.map((type) =>
        SYNC_CONFIG[type].fetcher(),
      );
      const results = await Promise.allSettled(fetchers);

      if (!isMounted) return;

      let anyRunning = false;

      setSyncState((prev) => {
        const next = { ...prev };

        const handleResult = (
          type: SyncType,
          result: PromiseSettledResult<SyncProgressResponse>,
        ) => {
          if (result.status !== "fulfilled") {
            return;
          }

          const data = result.value;
          const wasVisible = prev[type].isVisible;
          const wasRunning = Boolean(prev[type].data?.in_progress);
          const isRunning = Boolean(data.in_progress);
          const hasError = Boolean(data.error);

          if (isRunning) {
            anyRunning = true;
          }

          // Sync just completed - start fade out
          if (wasRunning && !isRunning && !hasError) {
            next[type] = {
              data,
              isVisible: true,
              isFadingOut: true,
            };

            // Clear any existing timeout
            if (fadeOutTimeouts[type]) {
              clearTimeout(fadeOutTimeouts[type]);
            }

            // Hide after fade-out animation completes
            fadeOutTimeouts[type] = setTimeout(() => {
              if (!isMounted) return;
              setSyncState((current) => ({
                ...current,
                [type]: {
                  ...current[type],
                  isVisible: false,
                  isFadingOut: false,
                },
              }));
            }, 2000); // 2s fade-out duration
          } else {
            next[type] = {
              data,
              isVisible: wasVisible || isRunning || hasError,
              isFadingOut: prev[type].isFadingOut,
            };
          }
        };

        enabledSyncTypes.forEach((type, index) => {
          handleResult(type, results[index]);
        });

        return next;
      });

      anySyncRunningRef.current = anyRunning;

      if (isMounted) {
        scheduleNextPoll();
      }
    };

    const scheduleNextPoll = () => {
      if (pollTimeout) clearTimeout(pollTimeout);

      if (document.visibilityState === "hidden") return;

      const interval = POLL_INTERVAL;

      pollTimeout = setTimeout(fetchProgress, interval);
    };

    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        fetchProgress();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);

    fetchProgress();

    return () => {
      isMounted = false;
      if (pollTimeout) clearTimeout(pollTimeout);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      Object.values(fadeOutTimeouts).forEach((timeout) => {
        if (timeout) clearTimeout(timeout);
      });
    };
  }, [enabledSyncTypes]);

  const visibleEntries = (
    Object.entries(syncState) as [SyncType, SyncState][]
  ).filter(
    ([type, state]) => enabledSyncTypes.includes(type) && state.isVisible,
  );

  if (visibleEntries.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <RefreshCw className="w-4 h-4 text-muted-foreground" />
        <p className="text-sm font-medium text-muted-foreground">
          Synchronization Progress
        </p>
      </div>

      <div className="space-y-4">
        {visibleEntries.map(([type, state]) => {
          const { data, isFadingOut } = state;
          const { Icon, label, accent } = SYNC_CONFIG[type];

          const resources = data?.resources ?? {};
          const hasResources = Object.keys(resources).length > 0;
          const isRunning = Boolean(data?.in_progress);
          const hasError = Boolean(data?.error);

          let statusMessage = "Sync just finished";
          if (isRunning) statusMessage = "Sync in progress...";
          else if (hasError) statusMessage = "Sync status unavailable";
          else if (isFadingOut) statusMessage = "Sync complete!";

          return (
            <div
              key={type}
              className={`rounded-lg border bg-muted/30 p-4 space-y-3 transition-all duration-[2000ms] ease-out ${
                isRunning ? "shadow-md shadow-primary/10 border-primary/30" : ""
              } ${isFadingOut ? "opacity-0 translate-y-2" : "opacity-100"}`}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Icon
                    className={`w-4 h-4 ${accent} ${
                      isRunning ? "animate-spin-slow" : ""
                    }`}
                  />
                  <div>
                    <p className="text-sm font-medium">{label}</p>
                    <p className="text-xs text-muted-foreground">
                      {statusMessage}
                    </p>
                  </div>
                </div>
                <Badge variant={isRunning ? "secondary" : "outline"}>
                  {isRunning ? "Running" : "Idle"}
                </Badge>
              </div>

              <div className="text-xs text-muted-foreground">
                Phase: {getPhaseLabel(data?.current_phase)}
              </div>

              {hasError && (
                <p className="text-xs text-destructive">
                  {data?.error || "Failed to load progress."}
                </p>
              )}

              {hasResources ? (
                <div className="space-y-3">
                  {Object.entries(resources).map(([resourceType, progress]) => {
                    const labelText = formatResourceName(resourceType);
                    const ResourceIcon = getResourceIcon(resourceType);

                    const progressLabel = `${progress.current} processed`;

                    return (
                      <div
                        key={resourceType}
                        className="space-y-1 rounded-md p-2 transition-all duration-300 hover:bg-muted/60"
                      >
                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-2">
                            <ResourceIcon
                              className={`w-4 h-4 text-muted-foreground ${
                                isRunning ? "animate-pulse" : ""
                              }`}
                            />
                            <span className="font-medium">{labelText}</span>
                          </div>
                          <span className="text-muted-foreground">
                            {progressLabel}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">
                  {isRunning
                    ? "Waiting for progress updates..."
                    : "No progress reported yet."}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
