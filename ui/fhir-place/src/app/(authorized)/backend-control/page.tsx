"use client";

import { RotateCcw, Trash2, RefreshCw } from "lucide-react";
import { OperationCard } from "@/components/custom/OperationCard";
import { ActionItem } from "@/components/custom/ActionItem";
import { ActionButton } from "@/components/custom/ActionButton";
import { ConfirmationDialog } from "@/components/custom/ConfirmationDialog";
import { useBackendControl } from "@/hooks/useBackendControl";
import { useConfirmationDialog } from "@/hooks/useConfirmationDialog";
import { useRef, useEffect, useState } from "react";
import SyncProgressDisplay, {
  type SyncProgressDisplayHandle,
} from "@/components/setup-wizard/SyncProgressDisplay";
import DeleteProgressDisplay, {
  type DeleteProgressDisplayHandle,
} from "@/components/setup-wizard/DeleteProgressDisplay";
import { getDeleteProgress } from "@/actions/backend/delete-progress";
import { getViableSyncTargets } from "@/actions/setup-wizard/getSystemSetup";
import { SyncTarget } from "@/types/setup-wizard/types";

export default function BackendControlPage() {
  const [syncTargets, setSyncTargets] = useState<SyncTarget[]>([]);
  const [isLoadingMode, setIsLoadingMode] = useState<boolean>(true);

  const {
    isLoading,
    lastResults,
    fadingBadges,
    handleSync,
    handleMiabisSync,
    handleDeleteAll,
    handleMiabisDelete,
  } = useBackendControl();

  const syncProgressRef = useRef<SyncProgressDisplayHandle>(null);
  const deleteProgressRef = useRef<DeleteProgressDisplayHandle>(null);

  useEffect(() => {
    const fetchSyncTargets = async () => {
      const targets = await getViableSyncTargets();
      setSyncTargets(targets);
      setIsLoadingMode(false);
    };
    fetchSyncTargets();
  }, []);

  const handleSyncWithProgress = async () => {
    syncProgressRef.current?.start(false);

    await handleSync();
  };

  const handleMiabisSyncWithProgress = async () => {
    syncProgressRef.current?.start(true);

    await handleMiabisSync();
  };

  const handleDeleteBlazeWithProgress = async () => {
    const initialProgress = await getDeleteProgress("blaze");

    if (initialProgress.success && initialProgress.resources) {
      const initialCounts: Record<string, number> = {};
      for (const resource of initialProgress.resources) {
        initialCounts[resource.resourceType] = resource.count;
      }

      deleteProgressRef.current?.start("blaze", initialCounts);
    } else {
      deleteProgressRef.current?.start("blaze");
    }

    await handleDeleteAll();
  };

  const handleDeleteMiabisWithProgress = async () => {
    const initialProgress = await getDeleteProgress("miabis");

    console.log("initialProgress", initialProgress);
    if (initialProgress.success && initialProgress.resources) {
      const initialCounts: Record<string, number> = {};
      for (const resource of initialProgress.resources) {
        initialCounts[resource.resourceType] = resource.count;
      }

      console.log("initialCounts", initialCounts);
      deleteProgressRef.current?.start("miabis", initialCounts);
    } else {
      console.log("initialProgress failed", initialProgress);
      deleteProgressRef.current?.start("miabis");
    }

    await handleMiabisDelete();
  };

  const {
    isDialogOpen: isDeleteBlazeDialogOpen,
    form: deleteBlazeForm,
    confirmationMessage: deleteBlazeConfirmMessage,
    handleConfirm: handleDeleteBlazeConfirm,
    handleDialogChange: handleDeleteBlazeDialogChange,
  } = useConfirmationDialog("DELETE ALL", handleDeleteBlazeWithProgress);

  const {
    isDialogOpen: isDeleteMiabisDialogOpen,
    form: deleteMiabisForm,
    confirmationMessage: deleteMiabisConfirmMessage,
    handleConfirm: handleDeleteMiabisConfirm,
    handleDialogChange: handleDeleteMiabisDialogChange,
  } = useConfirmationDialog("DELETE ALL", handleDeleteMiabisWithProgress);

  if (isLoadingMode) {
    return (
      <main className="flex-1 h-full flex flex-col p-6">
        <div className="flex items-center justify-center h-full">
          <p className="text-muted-foreground">Loading configuration...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 h-full flex flex-col p-6">
      <div className="flex-shrink-0 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">
              Backend Control
            </h2>
            <p className="text-muted-foreground">
              Manage and control your FHIR backend services
            </p>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <OperationCard
            title="Synchronization"
            description="Sync data from repositories to the FHIR server"
            icon={RotateCcw}
          >
            {(syncTargets.includes("blaze") ||
              syncTargets.includes("both")) && (
              <ActionItem
                title="Sync BLAZE"
                description="Sync patients, conditions, and samples"
                buttonText="Sync"
                onAction={handleSyncWithProgress}
                isLoading={isLoading === "Sync"}
                result={lastResults["Sync"]}
                isFading={fadingBadges["Sync"]}
                icon={RefreshCw}
                disabled={isLoading !== null}
              />
            )}

            {(syncTargets.includes("miabis") ||
              syncTargets.includes("both")) && (
              <ActionItem
                title="MIABIS Sync"
                description="Sync data using MIABIS on FHIR format"
                buttonText="MIABIS Sync"
                onAction={handleMiabisSyncWithProgress}
                isLoading={isLoading === "MIABIS Sync"}
                result={lastResults["MIABIS Sync"]}
                isFading={fadingBadges["MIABIS Sync"]}
                icon={RefreshCw}
                disabled={isLoading !== null}
              />
            )}
          </OperationCard>

          {/* Delete Operations */}
          <OperationCard
            title="Data Management"
            description="Delete operations for data cleanup"
            icon={Trash2}
          >
            {(syncTargets.includes("blaze") ||
              syncTargets.includes("both")) && (
              <ActionItem
                title="Delete Blaze Data"
                description="Remove all patients, conditions, and samples from Blaze"
                buttonText="Delete All"
                onAction={() => {}}
                isLoading={isLoading === "Delete All"}
                result={lastResults["Delete All"]}
                isFading={fadingBadges["Delete All"]}
                disabled={isLoading !== null}
              >
                <ConfirmationDialog
                  isOpen={isDeleteBlazeDialogOpen}
                  onOpenChange={handleDeleteBlazeDialogChange}
                  title="Are you sure?"
                  description="This action will delete all data from the Blaze FHIR server. This action cannot be undone."
                  confirmationMessage={deleteBlazeConfirmMessage}
                  confirmButtonText="Delete All"
                  form={deleteBlazeForm}
                  onConfirm={handleDeleteBlazeConfirm}
                  isLoading={isLoading !== null}
                >
                  <ActionButton
                    onClick={() => {}}
                    disabled={isLoading !== null}
                    loading={isLoading === "Delete All"}
                    icon={Trash2}
                    variant="destructive"
                  >
                    Delete All
                  </ActionButton>
                </ConfirmationDialog>
              </ActionItem>
            )}

            {(syncTargets.includes("miabis") ||
              syncTargets.includes("both")) && (
              <ActionItem
                title="Delete MIABIS Data"
                description="Remove all MIABIS data from MIABIS Blaze server"
                buttonText="Delete MIABIS"
                onAction={() => {}}
                isLoading={isLoading === "Delete MIABIS"}
                result={lastResults["Delete MIABIS"]}
                isFading={fadingBadges["Delete MIABIS"]}
                disabled={isLoading !== null}
              >
                <ConfirmationDialog
                  isOpen={isDeleteMiabisDialogOpen}
                  onOpenChange={handleDeleteMiabisDialogChange}
                  title="Are you sure?"
                  description="This action will delete all MIABIS data from the MIABIS FHIR server. This action cannot be undone."
                  confirmationMessage={deleteMiabisConfirmMessage}
                  confirmButtonText="Delete MIABIS"
                  form={deleteMiabisForm}
                  onConfirm={handleDeleteMiabisConfirm}
                  isLoading={isLoading !== null}
                >
                  <ActionButton
                    onClick={() => {}}
                    disabled={isLoading !== null}
                    loading={isLoading === "Delete MIABIS"}
                    icon={Trash2}
                    variant="destructive"
                  >
                    Delete MIABIS
                  </ActionButton>
                </ConfirmationDialog>
              </ActionItem>
            )}
          </OperationCard>
        </div>
      </div>

      {/* Progress Displays */}
      <div className="mt-6 flex-1 min-h-0 overflow-y-auto space-y-6 pr-2">
        <SyncProgressDisplay ref={syncProgressRef} />
        <DeleteProgressDisplay ref={deleteProgressRef} />
      </div>
    </main>
  );
}
