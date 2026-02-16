/* eslint-disable react-hooks/exhaustive-deps */
import { Code, Edit, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useState, useEffect, useContext } from "react";
import {
  CommonEnumMappingProps,
  EnumMapping,
  WizardState,
} from "@/types/setup-wizard/types";
import FreeTextVisualEditorComponent from "@/components/setup-wizard/type-to-collection-components/FreeTextVisualEditorComponent";
import ManualEditorComponent from "@/components/setup-wizard/enum-components/ManualEditorComponent";
import { SetupWizardContext } from "@/context/SetupWizardContext";

export default function DefineTypeToCollectionComponent({
  config,
  nextStep,
  previousStep,
}: CommonEnumMappingProps) {
  const { wizardStateMapping, wizardStateFetchFunction } = config;
  const [mappings, setMappings] = useState<EnumMapping[]>([
    { userValue: "", apiValue: "" },
  ]);

  const [activeTab, setActiveTab] = useState<"visual" | "manual">("visual");
  const [hasError, setHasError] = useState<boolean>(false);

  const { wizardState, setWizardState } = useContext(SetupWizardContext);

  useEffect(() => {
    const existingMappings = wizardStateFetchFunction(wizardState);
    if (existingMappings && existingMappings.length > 0) {
      setMappings(existingMappings);
    }
  }, []);

  const addMapping = () => {
    const newMappings = [...mappings, { userValue: "", apiValue: "" }];
    setMappings(newMappings);
  };

  const removeMapping = (index: number) => {
    const newMappings = mappings.filter((_, i) => i !== index);
    setMappings(newMappings);
  };

  const updateMapping = (
    index: number,
    field: keyof EnumMapping,
    value: string
  ) => {
    const updated = [...mappings];
    updated[index][field] = value;
    setMappings(updated);
  };

  const saveMapping = () => {
    setWizardState((prev: WizardState) => ({
      ...wizardStateMapping(prev, mappings),
    }));
    nextStep();
  };

  const handleManualJsonChange = (value: string, hasError: boolean) => {
    if (hasError) {
      setHasError(true);
      return;
    }

    const parsed = JSON.parse(value);

    const mappings = Object.entries(parsed).map(([userValue, apiValue]) => ({
      userValue,
      apiValue: apiValue as string,
    }));

    setMappings(mappings);

    setHasError(hasError || value.trim() === "{}");
  };

  return (
    <div className="h-full w-full flex flex-col">
      {/* Tabs for Visual/Manual mode */}
      <Tabs
        value={activeTab}
        onValueChange={(value) => setActiveTab(value as "visual" | "manual")}
        className="flex-1 flex flex-col min-h-0"
      >
        <TabsList className="grid w-full grid-cols-2 flex-shrink-0">
          <TabsTrigger
            value="visual"
            className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm"
            disabled={hasError}
          >
            <Edit className="h-3 w-3 sm:h-4 sm:w-4" />
            <span className="hidden xs:inline">Visual Editor</span>
            <span className="xs:hidden">Visual</span>
            {hasError && (
              <span className="hidden lg:inline text-xs sm:text-sm text-red-500 ml-2">
                (Fix errors in JSON to enable)
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger
            value="manual"
            className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm"
          >
            <Code className="h-3 w-3 sm:h-4 sm:w-4" />
            <span className="hidden xs:inline">Manual JSON</span>
            <span className="xs:hidden">JSON</span>
          </TabsTrigger>
        </TabsList>

        {/* Visual Editor Tab */}
        <TabsContent value="visual" className="flex-1 flex flex-col min-h-0">
          <FreeTextVisualEditorComponent
            mappings={mappings}
            addMapping={addMapping}
            updateMapping={updateMapping}
            removeMapping={removeMapping}
          />
        </TabsContent>

        {/* Manual JSON Tab */}
        <TabsContent value="manual" className="flex-1 flex flex-col min-h-0">
          <ManualEditorComponent
            currentMappings={mappings}
            availableOptions={[]}
            onChange={handleManualJsonChange}
            allowCustomValues={true}
          />
        </TabsContent>
      </Tabs>

      <div className="flex justify-between gap-2 pt-4">
        {previousStep && (
          <Button
            onClick={previousStep}
            variant="outline"
            className="flex items-center gap-1 sm:gap-2 h-8 sm:h-10 text-xs sm:text-sm px-2 sm:px-4"
          >
            <ArrowLeft className="w-3 h-3 sm:w-4 sm:h-4" />
            <span className="hidden xs:inline">Back</span>
          </Button>
        )}
        {!previousStep && <div></div>}
        <div className="flex gap-2">
          <Button
            disabled={mappings.length !== 0}
            onClick={() => nextStep()}
            variant="destructive"
            className="h-8 sm:h-10 text-xs sm:text-sm px-2 sm:px-4"
          >
            <span className="hidden md:inline">
              This mapping is not needed.{" "}
            </span>
            <span>Skip</span>
          </Button>
          <Button
            onClick={saveMapping}
            disabled={activeTab === "visual" ? mappings.length === 0 : hasError}
            className="h-8 sm:h-10 text-xs sm:text-sm px-3 sm:px-4"
          >
            Continue
          </Button>
        </div>
      </div>
    </div>
  );
}
