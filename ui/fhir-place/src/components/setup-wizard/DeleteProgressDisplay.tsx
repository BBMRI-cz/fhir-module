import {
  Trash2,
  Database,
  Building2,
  Users,
  FileText,
  TestTube,
  Layers,
} from "lucide-react";
import { Progress } from "@/components/ui/progress";
import {
  useState,
  useEffect,
  useCallback,
  forwardRef,
  useImperativeHandle,
  useRef,
} from "react";
import {
  getDeleteProgress,
  type DeleteProgressResponse,
} from "@/actions/backend/delete-progress";

const RESOURCE_ICONS = {
  Organization: Building2,
  Patient: Users,
  Condition: FileText,
  Specimen: TestTube,
  Group: Layers,
} as const;

const RESOURCE_ORDER = [
  "Organization",
  "Group",
  "Patient",
  "Condition",
  "Specimen",
] as const;

type ResourceType = (typeof RESOURCE_ORDER)[number];

interface ResourceCounts {
  [key: string]: {
    current: number;
    initial: number;
    percentage: number;
  };
}

export interface DeleteProgressDisplayHandle {
  start: (
    mode: "blaze" | "miabis",
    presetInitialCounts?: Record<string, number>
  ) => void;
  stop: () => void;
  reset: () => void;
}

interface DeleteProgressDisplayProps {
  onComplete?: () => void;
}

const DeleteProgressDisplay = forwardRef<
  DeleteProgressDisplayHandle,
  DeleteProgressDisplayProps
>(({ onComplete }, ref) => {
  const [resourceCounts, setResourceCounts] = useState<ResourceCounts>({});
  const [isPolling, setIsPolling] = useState(false);
  const [isCompleting, setIsCompleting] = useState(false);
  const [shouldRender, setShouldRender] = useState(false);
  const initialCountsRef = useRef<Record<string, number>>({});
  const [currentMode, setCurrentMode] = useState<"blaze" | "miabis" | null>(
    null
  );

  const fetchAllCounts = useCallback(async () => {
    if (!currentMode) {
      return;
    }

    try {
      const response: DeleteProgressResponse = await getDeleteProgress(
        currentMode
      );

      if (!response.success || !response.resources) {
        console.error("Failed to fetch delete progress:", response.error);
        return;
      }

      const counts: ResourceCounts = {};
      const trackedResourceTypes = Object.keys(initialCountsRef.current);

      for (const resource of response.resources) {
        const resourceType = resource.resourceType;

        if (
          trackedResourceTypes.length > 0 &&
          !trackedResourceTypes.includes(resourceType)
        ) {
          continue;
        }

        const current = resource.count;
        const initial = initialCountsRef.current[resourceType] || current;

        if (!initialCountsRef.current[resourceType]) {
          initialCountsRef.current[resourceType] = current;
        }

        const percentage =
          initial > 0 ? ((initial - current) / initial) * 100 : 0;

        counts[resourceType] = {
          current,
          initial,
          percentage: Math.min(100, Math.max(0, percentage)),
        };
      }

      setResourceCounts(counts);

      const trackedResources = Object.values(counts);
      const allZero =
        trackedResources.length > 0 &&
        trackedResources.every((count) => count.current === 0);

      // Also check if all initial counts were 0 (nothing to delete)
      const nothingToDelete =
        Object.keys(initialCountsRef.current).length > 0 &&
        Object.values(initialCountsRef.current).every((count) => count === 0);

      if ((allZero || nothingToDelete) && isPolling) {
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
      console.error("Error fetching delete progress:", error);
    }
  }, [isPolling, onComplete, currentMode]);

  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;

    if (isPolling) {
      fetchAllCounts();

      intervalId = setInterval(fetchAllCounts, 2000);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [isPolling, fetchAllCounts]);

  useImperativeHandle(ref, () => ({
    start: (
      mode: "blaze" | "miabis",
      presetInitialCounts?: Record<string, number>
    ) => {
      setCurrentMode(mode);
      setResourceCounts({});
      setIsCompleting(false);
      setShouldRender(true);

      if (presetInitialCounts) {
        initialCountsRef.current = presetInitialCounts;
      } else {
        initialCountsRef.current = {};
      }

      setTimeout(() => {
        setIsPolling(true);
      }, 50);
    },
    stop: () => {
      setIsPolling(false);
    },
    reset: () => {
      setCurrentMode(null);
      setResourceCounts({});
      initialCountsRef.current = {};
      setIsPolling(false);
      setIsCompleting(false);
      setShouldRender(false);
    },
  }));

  if (!shouldRender) {
    return null;
  }

  const hasData = Object.keys(resourceCounts).length > 0;
  const nothingToDelete =
    Object.keys(initialCountsRef.current).length > 0 &&
    Object.values(initialCountsRef.current).every((count) => count === 0);

  const getStatusMessage = () => {
    if (!isCompleting) {
      return "Deleting Resources...";
    }
    return nothingToDelete ? "No Data to Delete" : "Deletion Complete";
  };

  return (
    <div
      className={`space-y-4 pt-4 transition-opacity duration-[2000ms] ${
        isCompleting ? "opacity-0" : "opacity-100"
      }`}
    >
      <div className="flex items-center justify-center space-x-2">
        <Trash2
          className={`w-4 h-4 ${
            isCompleting ? "" : "animate-pulse text-destructive"
          }`}
        />
        <span className="text-sm font-medium">{getStatusMessage()}</span>
      </div>

      {hasData && (
        <div className="space-y-3">
          {Object.entries(resourceCounts)
            .sort((a, b) => {
              const orderA = RESOURCE_ORDER.indexOf(a[0] as ResourceType);
              const orderB = RESOURCE_ORDER.indexOf(b[0] as ResourceType);
              if (orderA !== -1 && orderB !== -1) return orderA - orderB;
              if (orderA !== -1) return -1;
              if (orderB !== -1) return 1;
              return a[0].localeCompare(b[0]);
            })
            .map(([resourceType, data]) => {
              const Icon =
                RESOURCE_ICONS[resourceType as keyof typeof RESOURCE_ICONS] ||
                Database;

              return (
                <div
                  key={resourceType}
                  className="space-y-2 p-3 bg-muted/50 rounded-lg"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Icon className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm font-medium">
                        {resourceType}
                      </span>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {data.current} remaining
                      {data.initial > 0 && ` (of ${data.initial})`}
                    </span>
                  </div>
                  <div className="space-y-1">
                    <Progress value={data.percentage} className="h-2" />
                    <div className="text-xs text-right text-muted-foreground">
                      {data.percentage.toFixed(1)}% deleted
                    </div>
                  </div>
                </div>
              );
            })}
        </div>
      )}

      {!hasData && !isCompleting && (
        <div className="text-center text-sm text-muted-foreground">
          {nothingToDelete
            ? "No resources found to delete"
            : "Loading resource counts..."}
        </div>
      )}
    </div>
  );
});

DeleteProgressDisplay.displayName = "DeleteProgressDisplay";

export default DeleteProgressDisplay;
