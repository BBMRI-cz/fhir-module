"use client";

import { Button } from "@/components/ui/button";
import { RotateCcw, Trash2, RefreshCw } from "lucide-react";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { CheckedFormInput } from "@/components/custom/form/CheckedFormInput";
import { Form } from "@/components/ui/form";
import { OperationCard } from "@/components/custom/OperationCard";
import { ActionItem } from "@/components/custom/ActionItem";
import { ActionButton } from "@/components/custom/ActionButton";
import { useBackendControl } from "@/hooks/useBackendControl";
import { useDeleteDialog } from "@/hooks/useDeleteDialog";

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
    isDeleteDialogOpen,
    form,
    deleteAllConfirmMessage,
    handleDelete,
    handleDialogChange,
  } = useDeleteDialog(handleDeleteAll);

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
              <Dialog
                open={isDeleteDialogOpen}
                onOpenChange={handleDialogChange}
              >
                <DialogTrigger asChild>
                  <ActionButton
                    onClick={() => {}}
                    disabled={isLoading !== null}
                    loading={isLoading === "Delete All"}
                    icon={Trash2}
                    variant="destructive"
                  >
                    Delete All
                  </ActionButton>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[425px]">
                  <DialogHeader>
                    <DialogTitle>Are you sure?</DialogTitle>
                    <DialogDescription>
                      This action will delete all data from the FHIR server.
                      This action cannot be undone. To proceed, please type
                      &quot;{deleteAllConfirmMessage}&quot; in the input field
                      below.
                    </DialogDescription>
                  </DialogHeader>
                  <Form {...form}>
                    <form onSubmit={form.handleSubmit(handleDelete)}>
                      <CheckedFormInput
                        control={form.control}
                        type="text"
                        name="confirmInput"
                        placeholder={deleteAllConfirmMessage}
                        errors={form.formState.errors}
                      />
                      <DialogFooter className="flex justify-end pt-4">
                        <DialogClose asChild>
                          <Button variant="outline">Cancel</Button>
                        </DialogClose>
                        <Button
                          type="submit"
                          disabled={isLoading !== null}
                          variant="destructive"
                          className="min-w-[100px]"
                        >
                          Delete All
                        </Button>
                      </DialogFooter>
                    </form>
                  </Form>
                </DialogContent>
              </Dialog>
            </ActionItem>

            <ActionItem
              title="Delete MIABIS Data"
              description="Remove all MIABIS on FHIR resources"
              buttonText="Delete MIABIS"
              onAction={handleMiabisDelete}
              isLoading={isLoading === "MIABIS Delete"}
              result={lastResults["MIABIS Delete"]}
              isFading={fadingBadges["MIABIS Delete"]}
              icon={Trash2}
              variant="destructive"
              disabled={isLoading !== null}
            />
          </OperationCard>
        </div>
      </div>
    </main>
  );
}
