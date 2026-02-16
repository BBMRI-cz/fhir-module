import { Code, ArrowLeft, File } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useState, useEffect, useContext, useCallback } from "react";
import {
  CustomMappingStepProps,
  DataMappingRecord,
  DataRecord,
} from "@/types/setup-wizard/types";
import { FieldMappingTab } from "@/components/setup-wizard/mapping-components/FieldMappingTab";
import { ManualJsonTab } from "@/components/setup-wizard/mapping-components/ManualJsonTab";
import {
  MappingContext,
  MappingContextProvider,
} from "@/context/MappingContext";
import { SetupWizardContext } from "@/context/SetupWizardContext";

function DefineMappingInner(props: CustomMappingStepProps) {
  const { previousStep, nextStep } = props;
  const { wizardStateMapping, title } = props.config;

  const { dataFields, dataFormat, setWizardState } =
    useContext(SetupWizardContext);
  const { data, setData } = useContext(MappingContext);

  const [activeTab, setActiveTab] = useState<"auto" | "manual">("auto");
  const [continueEnabled, setContinueEnabled] = useState<boolean>(false);

  const handleManualJsonChange = (
    newValues: Record<string, DataMappingRecord[]>,
    hasError: boolean
  ) => {
    if (hasError) {
      return;
    }

    const modifiedData = { ...data };
    for (const key in newValues) {
      if (modifiedData[key]) {
        modifiedData[key].mappings = newValues[key];
      }

      setData(modifiedData);
    }
  };

  useEffect(() => {
    let result = true;

    for (const key in data) {
      if (data[key].isRequired) {
        const field = data[key];

        if (field.onlyForFormats && field.onlyForFormats.length > 0) {
          if (dataFormat && !field.onlyForFormats.includes(dataFormat)) {
            continue;
          }
        }

        result &&= !!field.mappings.length;
      }
    }

    setContinueEnabled(result);
  }, [data, dataFormat]);

  const onClickNext = () => {
    setWizardState((prev) => ({
      ...wizardStateMapping(prev, data),
    }));

    if (nextStep) {
      nextStep();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="mb-2">
        <p className="text-xs md:text-sm text-gray-600">
          Map your data fields to FHIR standard. All required fields (*) must be
          mapped.
        </p>
      </div>

      <Tabs
        value={activeTab}
        onValueChange={(value) => setActiveTab(value as "auto" | "manual")}
        className="flex-1 flex flex-col min-h-0"
      >
        <TabsList className="grid w-full grid-cols-2 flex-shrink-0">
          <TabsTrigger
            value="auto"
            className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm"
          >
            <File className="w-3 h-3 sm:w-4 sm:h-4" />
            <span className="hidden sm:inline">Auto-Detected Fields</span>
            <span className="sm:hidden">Auto</span>
          </TabsTrigger>
          <TabsTrigger
            value="manual"
            className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm"
          >
            <Code className="w-3 h-3 sm:w-4 sm:h-4" />
            <span className="hidden sm:inline">Manual JSON</span>
            <span className="sm:hidden">JSON</span>
          </TabsTrigger>
        </TabsList>

        {/* Auto-Detected Fields Tab */}
        <TabsContent value="auto" className="flex-1 flex flex-col min-h-0">
          <FieldMappingTab mappingConceptName={title} />
        </TabsContent>

        {/* Manual JSON Tab */}
        <TabsContent value="manual" className="flex-1 flex flex-col min-h-0">
          <ManualJsonTab
            currentMappings={data}
            availableOptions={dataFields}
            onChange={handleManualJsonChange}
          />
        </TabsContent>
      </Tabs>

      {/* Footer */}
      <div className="flex justify-between gap-2 pt-4 flex-shrink-0">
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
        <Button
          onClick={onClickNext}
          disabled={!continueEnabled}
          className="h-8 sm:h-10 text-xs sm:text-sm px-3 sm:px-4"
        >
          Continue
        </Button>
      </div>
    </div>
  );
}

export default function DefineMappingComponent(props: CustomMappingStepProps) {
  const { getMappingSchema, wizardStateFetchFunction } = props.config;

  const { dataFormat, wizardState } = useContext(SetupWizardContext);

  const [initialDataMappings, setInitialDataMappings] = useState<
    Record<string, DataRecord>
  >(wizardStateFetchFunction(wizardState));

  const fetchSchema = useCallback(async () => {
    try {
      const schema = await getMappingSchema();

      const currentState = props.config.wizardStateFetchFunction(wizardState);

      const dataMappings: Record<string, DataRecord> = {};
      for (const key in schema) {
        if (
          dataFormat === "xml" &&
          schema[key].onlyForFormats?.length &&
          !schema[key].onlyForFormats?.includes("xml")
        ) {
          continue;
        }

        dataMappings[key] = {
          isRequired: schema[key].required,
          mappings: currentState[key]?.mappings || [],
          resultPath: schema[key].saveToPath,
          xmlDependsOn: schema[key].xmlDependsOn,
          onlyForFormats: schema[key].onlyForFormats,
        };
      }

      setInitialDataMappings(dataMappings);
    } catch (err) {
      console.error("Error fetching mapping schema:", err);
    }
  }, [getMappingSchema, props.config, wizardState, dataFormat]);

  useEffect(() => {
    fetchSchema();
  }, [fetchSchema]);

  return (
    <MappingContextProvider initialData={initialDataMappings}>
      <DefineMappingInner {...props} />
    </MappingContextProvider>
  );
}
