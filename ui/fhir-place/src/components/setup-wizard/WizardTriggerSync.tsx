"use client";

import {
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Database,
  ArrowRight,
  ArrowLeft,
  Save,
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
import { useContext, useState, useEffect } from "react";
import { SetupWizardContext } from "@/context/SetupWizardContext";
import writeAndSynchronize from "@/actions/setup-wizard/writeAndSynchronize";
import { Button } from "@/components/ui/button";
import { markSetupComplete } from "@/actions/setup-wizard/setup-status";
import SyncProgressDisplay from "@/components/setup-wizard/SyncProgressDisplay";

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
  const [configSaved, setConfigSaved] = useState(false);
  const [isSavingConfig, setIsSavingConfig] = useState(false);
  const [configSaveError, setConfigSaveError] = useState<string | null>(null);
  const [hasStartedAction, setHasStartedAction] = useState(false);

  const { isLoading, lastResults, fadingBadges, handleSync, handleMiabisSync } =
    useBackendControl();

  useEffect(() => {
    if (syncDone || configSaved) {
      markSetupComplete();
    }
  }, [syncDone, configSaved]);

  const saveConfigurationOnly = async () => {
    setHasStartedAction(true);
    setIsSavingConfig(true);
    setConfigSaveError(null);
    setConfigSaved(false);

    const result = await writeAndSynchronize(
      wizardState,
      dataFormat!,
      dataFolderPath!,
      csvSeparator
    );

    setIsSavingConfig(false);

    if (!result.success) {
      setConfigSaveError(
        result.errors?.[0] || "Failed to save configuration. Please try again."
      );
      return;
    }

    setConfigSaved(true);
  };

  const performTheChangeAndSync = async () => {
    setHasStartedAction(true);
    setConfigSaved(false);
    setConfigSaveError(null);

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

    if (wizardState.syncTarget === "both") {
      await Promise.all([handleSync(), handleMiabisSync()]);
    } else if (wizardState.syncTarget === "miabis") {
      await handleMiabisSync();
    } else {
      await handleSync();
    }

    setIsSyncing(false);
    setSyncDone(true);
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
            Save your configuration, or save and start the synchronization
            process to sync all patients, conditions, and samples from your
            configured repositories to the FHIR server.
          </p>

          <div className="space-y-4">
            <div className="flex gap-3">
              <ActionButton
                onClick={saveConfigurationOnly}
                disabled={isSyncing || isLoading !== null || isSavingConfig}
                loading={isSavingConfig}
                icon={Save}
                className="flex-1 min-w-[140px] h-12"
                variant="outline"
              >
                {isSavingConfig ? "Saving..." : "Save Config Only"}
              </ActionButton>
              <ActionButton
                onClick={performTheChangeAndSync}
                disabled={isSyncing || isLoading !== null || isSavingConfig}
                loading={isLoadingSync}
                icon={RefreshCw}
                className="flex-1 min-w-[140px] h-12"
              >
                {isSyncing ? "Syncing..." : "Save & Sync"}
              </ActionButton>
            </div>

            {/* Sync Progress Display */}
            <SyncProgressDisplay />

            {/* Completion Status */}
            {syncDone && (
              <div className="space-y-2 pt-4">
                <Badge variant="default" className="w-full justify-center py-2">
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Sync Completed Successfully
                </Badge>
              </div>
            )}

            {/* Config Saved Status */}
            {configSaved && !syncDone && (
              <div className="space-y-2 pt-4">
                <Badge
                  variant="secondary"
                  className="w-full justify-center py-2"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Configuration Saved Successfully
                </Badge>
              </div>
            )}

            {/* Config Save Error */}
            {configSaveError && (
              <div className="space-y-2">
                <Badge
                  variant="destructive"
                  className="w-full justify-center py-2"
                >
                  <AlertCircle className="w-3 h-3 mr-1" />
                  Configuration Save Failed
                </Badge>
                <p className="text-sm text-red-600 text-center">
                  {configSaveError}
                </p>
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
          <Button
            onClick={() => nextStep()}
            disabled={!hasStartedAction}
            size="sm"
          >
            Continue
            <ArrowRight className="w-3 h-3 ml-1" />
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
