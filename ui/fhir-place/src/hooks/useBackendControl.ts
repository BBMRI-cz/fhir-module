import { useState } from "react";
import { toast } from "sonner";
import {
  syncAction,
  miabisSyncAction,
  deleteAllAction,
  miabisDeleteAction,
  type BackendActionResult,
} from "@/actions/backend/backend-control";
import { type ActionResult } from "@/components/custom/ActionItem";

export function useBackendControl() {
  const [isLoading, setIsLoading] = useState<string | null>(null);
  const [lastResults, setLastResults] = useState<Record<string, ActionResult>>(
    {}
  );
  const [fadingBadges, setFadingBadges] = useState<Record<string, boolean>>({});

  const handleAction = async (
    actionName: string,
    actionFunction: () => Promise<BackendActionResult>
  ) => {
    setIsLoading(actionName);
    try {
      const result = await actionFunction();
      setLastResults((prev) => ({ ...prev, [actionName]: result }));

      setFadingBadges((prev) => ({ ...prev, [actionName]: false }));
      setTimeout(() => {
        setFadingBadges((prev) => ({ ...prev, [actionName]: true }));
      }, 3000);

      setTimeout(() => {
        setLastResults((prev) => {
          const newResults = { ...prev };
          delete newResults[actionName];
          return newResults;
        });
        setFadingBadges((prev) => {
          const newFading = { ...prev };
          delete newFading[actionName];
          return newFading;
        });
      }, 4000);

      if (result.success) {
        toast.success(`${actionName} Success`, {
          description: result.message,
        });
      } else {
        toast.error(`${actionName} Failed`, {
          description: result.message,
        });
      }
    } catch {
      toast.error(`${actionName} Failed`, {
        description: "An unexpected error occurred",
      });
    } finally {
      setIsLoading(null);
    }
  };

  const handleSync = () => handleAction("Sync", syncAction);
  const handleMiabisSync = () => handleAction("MIABIS Sync", miabisSyncAction);
  const handleDeleteAll = () => handleAction("Delete All", deleteAllAction);
  const handleMiabisDelete = () =>
    handleAction("MIABIS Delete", miabisDeleteAction);

  return {
    isLoading,
    lastResults,
    fadingBadges,
    handleSync,
    handleMiabisSync,
    handleDeleteAll,
    handleMiabisDelete,
  };
}
