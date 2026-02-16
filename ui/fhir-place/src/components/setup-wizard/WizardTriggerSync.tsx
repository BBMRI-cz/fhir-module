"use client";

import {
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Database,
  ArrowRight,
  ArrowLeft,
} from "lucide-react";
import { ActionButton } from "@/components/custom/ActionButton";
import { useBackendControl } from "@/hooks/useBackendControl";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useContext, useState, useRef, useEffect } from "react";
import { SetupWizardContext } from "@/context/SetupWizardContext";
import writeAndSynchronize from "@/actions/setup-wizard/writeAndSynchronize";
import { Button } from "@/components/ui/button";
import SyncProgressDisplay, {
  type SyncProgressDisplayHandle,
} from "@/components/setup-wizard/SyncProgressDisplay";
import { markSetupComplete } from "@/actions/setup-wizard/setup-status";

export default function WizardTriggerSync() {
  const {
    nextStep,
    previousStep,
    wizardState,
    dataFormat,
    dataFolderPath,
    csvSeparator,
  } = useContext(SetupWizardContext);

  const [syncDone, setSyncDone] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const blazeSyncProgressRef = useRef<SyncProgressDisplayHandle>(null);
  const miabisSyncProgressRef = useRef<SyncProgressDisplayHandle>(null);
  const [completedSyncs, setCompletedSyncs] = useState<Set<string>>(new Set());

  const { isLoading, lastResults, fadingBadges, handleSync, handleMiabisSync } =
    useBackendControl();

  const handleSyncComplete = (syncType: string) => {
    setCompletedSyncs((prev) => {
      const newSet = new Set(prev);
      newSet.add(syncType);

      // Check if all required syncs are complete
      const isBoth = wizardState.syncTarget === "both";
      const allComplete = isBoth
        ? newSet.has("blaze") && newSet.has("miabis")
        : newSet.size > 0;

      if (allComplete) {
        setSyncDone(true);
        setIsSyncing(false);
      }

      return newSet;
    });
  };

  useEffect(() => {
    if (syncDone) {
      markSetupComplete();
    }
  }, [syncDone]);

  const performTheChangeAndSync = async () => {
    const result = await writeAndSynchronize(
      wizardState,
      dataFormat!,
      dataFolderPath!,
      csvSeparator
    );

    if (!result.success) {
      return;
    }

    setSyncDone(false);
    setIsSyncing(true);
    setCompletedSyncs(new Set());

    // Sync based on the selected targets
    if (wizardState.syncTarget === "both") {
      // Start both syncs in parallel
      blazeSyncProgressRef.current?.start(false);
      miabisSyncProgressRef.current?.start(true);
      await Promise.all([handleSync(), handleMiabisSync()]);
    } else if (wizardState.syncTarget === "miabis") {
      miabisSyncProgressRef.current?.start(true);
      await handleMiabisSync();
    } else {
      blazeSyncProgressRef.current?.start(false);
      await handleSync();
    }
  };

  const syncResult = lastResults["Sync"];
  const isLoadingSync = isLoading === "Sync";
  const isFadingSync = fadingBadges["Sync"];

  return (
    <div className="flex flex-col items-center justify-start min-h-full w-full p-6 pt-0 overflow-auto">
      <Card className="w-full max-w-2xl">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 p-3 bg-blue-100 rounded-full w-fit">
            <Database className="w-12 h-12 text-blue-600" />
          </div>
          <CardTitle className="text-2xl font-bold">
            Trigger Sync Process
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <p className="text-muted-foreground text-center">
            Click the button below to start the synchronization process. This
            will sync all patients, conditions, and samples from your configured
            repositories to the FHIR server.
          </p>

          <div className="space-y-4">
            <ActionButton
              onClick={performTheChangeAndSync}
              disabled={isSyncing || isLoading !== null}
              loading={isLoadingSync}
              icon={RefreshCw}
              className="w-full min-w-[160px] h-12"
            >
              {isSyncing ? "Syncing..." : "Start Sync"}
            </ActionButton>

            {/* Sync Progress - Always render both to avoid hooks issues */}
            <div className="space-y-6">
              {/* BLAZE Sync Progress */}
              <div
                className={`space-y-2 ${
                  wizardState.syncTarget === "miabis" ? "hidden" : ""
                }`}
              >
                {wizardState.syncTarget === "both" && (
                  <div className="flex items-center justify-center gap-2">
                    <h3 className="text-sm font-semibold text-center">
                      BLAZE FHIR Server Sync
                    </h3>
                    {completedSyncs.has("blaze") && (
                      <CheckCircle className="w-4 h-4 text-green-600" />
                    )}
                  </div>
                )}
                <SyncProgressDisplay
                  ref={blazeSyncProgressRef}
                  onComplete={() => handleSyncComplete("blaze")}
                />
              </div>

              {/* MIABIS Sync Progress */}
              <div
                className={`space-y-2 ${
                  wizardState.syncTarget === "blaze" ? "hidden" : ""
                }`}
              >
                {wizardState.syncTarget === "both" && (
                  <div className="flex items-center justify-center gap-2">
                    <h3 className="text-sm font-semibold text-center">
                      MIABIS FHIR Server Sync
                    </h3>
                    {completedSyncs.has("miabis") && (
                      <CheckCircle className="w-4 h-4 text-green-600" />
                    )}
                  </div>
                )}
                <SyncProgressDisplay
                  ref={miabisSyncProgressRef}
                  onComplete={() => handleSyncComplete("miabis")}
                />
              </div>
            </div>

            {/* Completion Status */}
            {syncDone && (
              <div className="space-y-2 pt-4">
                <Badge variant="default" className="w-full justify-center py-2">
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Sync Completed Successfully
                </Badge>
              </div>
            )}

            {/* Error Status */}
            {syncResult && !syncResult.success && (
              <div className="space-y-2">
                <Badge
                  variant="destructive"
                  className={`transition-opacity duration-1000 ${
                    isFadingSync ? "opacity-50" : "opacity-100"
                  }`}
                >
                  <AlertCircle className="w-3 h-3 mr-1" />
                  Sync Failed
                </Badge>

                {syncResult.message && (
                  <p
                    className={`text-sm transition-opacity duration-1000 ${
                      isFadingSync ? "opacity-50" : "opacity-100"
                    } text-red-600`}
                  >
                    {syncResult.message}
                  </p>
                )}
              </div>
            )}

            {isLoadingSync && !isSyncing && (
              <div className="text-sm text-muted-foreground animate-pulse text-center">
                Initializing sync...
              </div>
            )}
          </div>
        </CardContent>
        <CardFooter className="flex justify-between p-6 pt-0">
          <Button onClick={() => previousStep()} size="sm" disabled={isSyncing}>
            <ArrowLeft className="w-3 h-3 mr-1" />
            Back
          </Button>
          <Button onClick={() => nextStep()} disabled={!syncDone} size="sm">
            Continue
            <ArrowRight className="w-3 h-3 ml-1" />
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
