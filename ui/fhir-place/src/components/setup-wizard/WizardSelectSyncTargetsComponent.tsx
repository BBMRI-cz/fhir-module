"use client";

import { useContext, useEffect, useState } from "react";
import { SetupWizardContext } from "@/context/SetupWizardContext";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ArrowRight, Database, GitBranch } from "lucide-react";
import { SyncTarget } from "@/types/setup-wizard/types";
import { cn } from "@/lib/utils";
import { getViableSyncTargets } from "@/actions/setup-wizard/getSystemSetup";

export default function WizardSelectSyncTargetsComponent() {
  const { nextStep, previousStep, wizardState, setWizardState } =
    useContext(SetupWizardContext);

  const [viableSyncTargets, setViableSyncTargets] = useState<SyncTarget[]>([]);

  useEffect(() => {
    const fetchViableSyncTargets = async () => {
      const viableSyncTargets = await getViableSyncTargets();
      setViableSyncTargets(viableSyncTargets);
    };
    fetchViableSyncTargets();
  }, []);

  const handleSelectTarget = (target: SyncTarget) => {
    setWizardState((prev) => ({
      ...prev,
      syncTarget: target,
    }));
  };

  const selectedTarget = wizardState.syncTarget;

  const syncOptions = [
    {
      value: "blaze" as SyncTarget,
      title: "BLAZE Only",
      description: "Sync data to standard FHIR BLAZE server",
      icon: Database,
    },
    {
      value: "miabis" as SyncTarget,
      title: "MIABIS Only",
      description: "Sync data to MIABIS on FHIR server",
      icon: Database,
    },
    {
      value: "both" as SyncTarget,
      title: "Both BLAZE & MIABIS",
      description: "Sync data to both servers with separate configurations",
      icon: GitBranch,
    },
  ].filter((option) => viableSyncTargets.includes(option.value));

  return (
    <div className="flex flex-col items-center justify-start min-h-full w-full p-6 pt-0 overflow-auto">
      <Card className="w-full max-w-2xl">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 p-3 bg-blue-100 rounded-full w-fit">
            <GitBranch className="w-12 h-12 text-blue-600" />
          </div>
          <CardTitle className="text-2xl font-bold">
            Select Sync Targets
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <p className="text-muted-foreground text-center">
            Choose which FHIR servers you want to synchronize your data to. You
            can select a single target or both.
          </p>

          <div className="grid gap-4">
            {syncOptions.map((option) => {
              const Icon = option.icon;
              const isSelected = selectedTarget === option.value;

              return (
                <button
                  key={option.value}
                  onClick={() => handleSelectTarget(option.value)}
                  className={cn(
                    "p-4 rounded-lg border-2 transition-all duration-200 text-left hover:shadow-md",
                    isSelected
                      ? "border-green-500 bg-primary/5 shadow-sm"
                      : "border-gray-200 hover:border-primary/50"
                  )}
                >
                  <div className="flex items-start gap-4">
                    <div
                      className={cn(
                        "p-2 rounded-lg",
                        isSelected
                          ? "bg-primary/10 text-primary"
                          : "bg-gray-100 text-gray-600"
                      )}
                    >
                      <Icon className="w-6 h-6" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg mb-1">
                        {option.title}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {option.description}
                      </p>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {selectedTarget === "both" && (
            <div className="p-4 border rounded-lg">
              <p className="text-sm">
                <strong>Note:</strong> When selecting both targets, you&apos;ll
                configure mappings for BLAZE first. The MIABIS configuration
                will be pre-filled with your BLAZE values to speed up the
                process, and you can modify them as needed.
              </p>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex justify-between p-6 pt-0">
          <Button onClick={() => previousStep()} size="sm">
            <ArrowLeft className="w-3 h-3 mr-1" />
            Back
          </Button>
          <Button
            onClick={() => nextStep()}
            size="sm"
            disabled={!selectedTarget}
          >
            Continue
            <ArrowRight className="w-3 h-3 ml-1" />
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
