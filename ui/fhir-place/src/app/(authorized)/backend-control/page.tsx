"use client";

import { RotateCcw, Trash2, RefreshCw } from "lucide-react";
import { OperationCard } from "@/components/custom/OperationCard";
import { ActionItem } from "@/components/custom/ActionItem";
import { ActionButton } from "@/components/custom/ActionButton";
import { ConfirmationDialog } from "@/components/custom/ConfirmationDialog";
import { useBackendControl } from "@/hooks/useBackendControl";
import { useConfirmationDialog } from "@/hooks/useConfirmationDialog";

export default function BackendControlPage() {
  const {
    isLoading,
    lastResults,
    fadingBadges,
    handleSync,
    handleMiabisSync,
    handleDeleteAll,
    handleMiabisDelete,
  } = useBackendControl();

  const {
    isDialogOpen: isDeleteAllDialogOpen,
    form: deleteAllForm,
    confirmationMessage: deleteAllConfirmMessage,
    handleConfirm: handleDeleteAllConfirm,
    handleDialogChange: handleDeleteAllDialogChange,
  } = useConfirmationDialog("DELETE ALL", handleDeleteAll);

  const {
    isDialogOpen: isMiabisDeleteDialogOpen,
    form: miabisDeleteForm,
    confirmationMessage: miabisDeleteConfirmMessage,
    handleConfirm: handleMiabisDeleteConfirm,
    handleDialogChange: handleMiabisDeleteDialogChange,
  } = useConfirmationDialog("DELETE ALL", handleMiabisDelete);

  return (
    <main className="flex-1 p-6">
      <div className="space-y-6">
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
            <ActionItem
              title="Standard Sync"
              description="Sync patients, conditions, and samples"
              buttonText="Sync"
              onAction={handleSync}
              isLoading={isLoading === "Sync"}
              result={lastResults["Sync"]}
              isFading={fadingBadges["Sync"]}
              icon={RefreshCw}
              disabled={isLoading !== null}
            />

            <ActionItem
              title="MIABIS Sync"
              description="Sync data using MIABIS on FHIR format"
              buttonText="MIABIS Sync"
              onAction={handleMiabisSync}
              isLoading={isLoading === "MIABIS Sync"}
              result={lastResults["MIABIS Sync"]}
              isFading={fadingBadges["MIABIS Sync"]}
              icon={RefreshCw}
              disabled={isLoading !== null}
            />
          </OperationCard>

          {/* Delete Operations */}
          <OperationCard
            title="Data Management"
            description="Delete operations for data cleanup"
            icon={Trash2}
          >
            <ActionItem
              title="Delete All Data"
              description="Remove all patients, conditions, and samples"
              buttonText="Delete All"
              onAction={() => {}}
              isLoading={isLoading === "Delete All"}
              result={lastResults["Delete All"]}
              isFading={fadingBadges["Delete All"]}
              disabled={isLoading !== null}
            >
              <ConfirmationDialog
                isOpen={isDeleteAllDialogOpen}
                onOpenChange={handleDeleteAllDialogChange}
                title="Are you sure?"
                description="This action will delete all data from the FHIR server. This action cannot be undone."
                confirmationMessage={deleteAllConfirmMessage}
                confirmButtonText="Delete All"
                form={deleteAllForm}
                onConfirm={handleDeleteAllConfirm}
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

            <ActionItem
              title="Delete MIABIS Data"
              description="Remove all MIABIS on FHIR resources"
              buttonText="Delete MIABIS"
              onAction={() => {}}
              isLoading={isLoading === "MIABIS Delete"}
              result={lastResults["MIABIS Delete"]}
              isFading={fadingBadges["MIABIS Delete"]}
              disabled={isLoading !== null}
            >
              <ConfirmationDialog
                isOpen={isMiabisDeleteDialogOpen}
                onOpenChange={handleMiabisDeleteDialogChange}
                title="Are you sure?"
                description="This action will delete all MIABIS data from the FHIR server. This action cannot be undone."
                confirmationMessage={miabisDeleteConfirmMessage}
                confirmButtonText="Delete MIABIS"
                form={miabisDeleteForm}
                onConfirm={handleMiabisDeleteConfirm}
                isLoading={isLoading !== null}
              >
                <ActionButton
                  onClick={() => {}}
                  disabled={isLoading !== null}
                  loading={isLoading === "MIABIS Delete"}
                  icon={Trash2}
                  variant="destructive"
                >
                  Delete MIABIS
                </ActionButton>
              </ConfirmationDialog>
            </ActionItem>
          </OperationCard>
        </div>
      </div>
    </main>
  );
}
