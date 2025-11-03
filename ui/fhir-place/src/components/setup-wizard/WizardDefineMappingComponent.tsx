"use client";
import { FileText } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useContext, useState } from "react";
import { DefinitionStep } from "@/types/setup-wizard/types";
import DefineMappingComponent from "@/components/setup-wizard/DefineMappingComponent";
import DefineTypeToCollectionComponent from "@/components/setup-wizard/DefineTypeToCollectionComponent";
import {
  conditionMappingConfig,
  donorMappingConfig,
  sampleMappingConfig,
  typeToCollectionConfig,
} from "@/lib/setup-wizard/mapping-configs";
import { SetupWizardContext } from "@/context/SetupWizardContext";

export default function WizardDefineMappingComponent() {
  const { nextStep, previousStep } = useContext(SetupWizardContext);

  const [definitionStep, setDefinitionStep] =
    useState<DefinitionStep>("typeToCollection");

  return (
    <div className="h-full bg-gradient-to-br overflow-hidden">
      <div className="h-full flex flex-col">
        <Card className="border-0 shadow-xl backdrop-blur-sm h-full flex flex-col gap-2">
          <CardHeader className="flex-shrink-0">
            <CardTitle className="text-xl font-semibold flex items-center text-md lg:text-2xl">
              <FileText className="w-5 h-5" />
              {definitionStep.charAt(0).toUpperCase() +
                definitionStep.slice(1)}{" "}
              Mapping
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-auto">
            {definitionStep === "typeToCollection" && (
              <DefineTypeToCollectionComponent
                config={typeToCollectionConfig}
                nextStep={() => setDefinitionStep("donor")}
                previousStep={() => previousStep()}
              />
            )}
            {definitionStep === "donor" && (
              <DefineMappingComponent
                config={donorMappingConfig}
                nextStep={() => setDefinitionStep("condition")}
                previousStep={() => setDefinitionStep("typeToCollection")}
              />
            )}
            {definitionStep === "condition" && (
              <DefineMappingComponent
                config={conditionMappingConfig}
                nextStep={() => setDefinitionStep("sample")}
                previousStep={() => setDefinitionStep("donor")}
              />
            )}
            {definitionStep === "sample" && (
              <DefineMappingComponent
                config={sampleMappingConfig}
                nextStep={() => nextStep()}
                previousStep={() => setDefinitionStep("condition")}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
