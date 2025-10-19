"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText } from "lucide-react";
import DefineEnumMappingComponent from "@/components/setup-wizard/DefineEnumMappingComponent";
import {
  EnumDefinitionStep,
  SyncTargetConfig,
} from "@/types/setup-wizard/types";
import { useContext, useState } from "react";
import {
  materialConfig,
  temperatureConfig,
} from "@/lib/setup-wizard/mapping-configs";
import { SetupWizardContext } from "@/context/SetupWizardContext";

export interface WizardDefineEnumGroupMappingComponentProps {
  targetConfig: SyncTargetConfig;
}

const resolveModeLabel = (
  targetConfig: SyncTargetConfig
): string | undefined => {
  if (targetConfig === "blazeConfig") {
    return "BLAZE";
  } else if (targetConfig === "miabisConfig") {
    return "MIABIS";
  }
  return undefined;
};

export default function WizardDefineEnumGroupMappingComponent({
  targetConfig,
}: WizardDefineEnumGroupMappingComponentProps) {
  const { nextStep, previousStep } = useContext(SetupWizardContext);

  const [definitionStep, setDefinitionStep] =
    useState<EnumDefinitionStep>("temperature");

  return (
    <div className="h-full bg-gradient-to-br overflow-hidden">
      <div className="h-full flex flex-col">
        <Card className="border-0 shadow-xl backdrop-blur-sm h-full flex flex-col gap-2">
          <CardHeader className="flex-shrink-0">
            <CardTitle className="text-xl font-semibold flex flex-col gap-1 text-md lg:text-2xl">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                <span>
                  {definitionStep.charAt(0).toUpperCase() +
                    definitionStep.slice(1)}{" "}
                  Mapping
                </span>
                {resolveModeLabel(targetConfig) && (
                  <span className="text-sm font-normal text-muted-foreground">
                    ({resolveModeLabel(targetConfig)})
                  </span>
                )}
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-auto">
            {definitionStep === "temperature" && (
              <DefineEnumMappingComponent
                config={temperatureConfig}
                nextStep={() => setDefinitionStep("material")}
                previousStep={() => previousStep()}
                targetConfig={targetConfig}
              />
            )}
            {definitionStep === "material" && (
              <DefineEnumMappingComponent
                config={materialConfig}
                nextStep={() => nextStep()}
                previousStep={() => setDefinitionStep("temperature")}
                targetConfig={targetConfig}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
