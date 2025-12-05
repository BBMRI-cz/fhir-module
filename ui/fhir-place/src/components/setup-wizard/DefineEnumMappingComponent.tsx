/* eslint-disable react-hooks/exhaustive-deps */
import { Code, Edit, ArrowLeft, AlertTriangle, FileSearch } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  HoverCard,
  HoverCardTrigger,
  HoverCardContent,
} from "@/components/ui/hover-card";
import { useState, useEffect, useContext, useMemo } from "react";
import {
  DefineEnumMappingProps,
  EnumMapping,
  WizardState,
} from "@/types/setup-wizard/types";
import LoadingComponent from "@/components/setup-wizard/common/LoadingComponent";
import ErrorComponent from "@/components/setup-wizard/common/ErrorComponent";
import VisualEditorComponent from "@/components/setup-wizard/enum-components/VisualEditorComponent";
import ManualEditorComponent from "@/components/setup-wizard/enum-components/ManualEditorComponent";
import ExtractValuesDialog from "@/components/setup-wizard/enum-components/ExtractValuesDialog";
import { SetupWizardContext } from "@/context/SetupWizardContext";

export default function DefineEnumMappingComponent({
  config,
  nextStep,
  previousStep,
  targetConfig,
}: DefineEnumMappingProps) {
  const {
    dataFetcher,
    wizardStateMapping,
    wizardStateFetchFunction,
    allowCustomValuesGetter,
    allowCustomValuesSetter,
  } = config;
  const [mappings, setMappings] = useState<EnumMapping[]>([
    { userValue: "", apiValue: "" },
  ]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<"visual" | "manual">("visual");

  const [enumData, setEnumData] = useState<string[] | null>(null);

  const [hasError, setHasError] = useState<boolean>(false);

  const { wizardState, setWizardState, dataFormat, dataFolderPath } =
    useContext(SetupWizardContext);

  const [isExtractDialogOpen, setIsExtractDialogOpen] = useState(false);

  const allowCustomValues = allowCustomValuesGetter(wizardState, targetConfig);

  const setAllowCustomValues = (value: boolean) => {
    setWizardState((prev: WizardState) =>
      allowCustomValuesSetter(prev, targetConfig, value)
    );
  };

  const hasCustomValues = mappings.some(
    (mapping) =>
      mapping.apiValue && enumData && !enumData.includes(mapping.apiValue)
  );

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await dataFetcher(targetConfig === "miabisConfig");
        setEnumData(data);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : `Failed to load ${config.title.toLowerCase()} data`
        );
        console.error(
          `Error fetching ${config.title.toLowerCase()} data:`,
          err
        );
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [config, dataFetcher]);

  useEffect(() => {
    const existingMappings = wizardStateFetchFunction(
      wizardState,
      targetConfig
    );
    setMappings(existingMappings);
  }, []);

  useEffect(() => {
    if (hasCustomValues && !allowCustomValues) {
      setAllowCustomValues(true);
    }
  }, [hasCustomValues, allowCustomValues]);

  const getAvailableOptions = () => {
    return enumData ?? [];
  };

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
      ...wizardStateMapping(prev, targetConfig, mappings),
    }));
    nextStep();
  };

  const existingUserValues = useMemo(
    () => new Set(mappings.map((m) => m.userValue)),
    [mappings]
  );

  const handleExtractedValues = (newValues: string[]) => {
    const newMappings: EnumMapping[] = newValues.map((value) => ({
      userValue: value,
      apiValue: "",
    }));
    setMappings((prev) => [...prev, ...newMappings]);
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

  if (loading) {
    return <LoadingComponent />;
  }

  if (error) {
    return <ErrorComponent message={error} />;
  }

  const availableOptions = getAvailableOptions();

  return (
    <div className="h-full w-full flex flex-col">
      {/* Custom Values Checkbox with Warning */}
      <div className="mb-4 p-3 border rounded-lg bg-muted/30">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <Checkbox
              id="allow-custom-values"
              checked={allowCustomValues}
              onCheckedChange={(checked) =>
                setAllowCustomValues(checked === true)
              }
              disabled={hasCustomValues}
              className="mt-0.5"
            />
            <div className="flex-1 flex items-center gap-2">
              <Label
                htmlFor="allow-custom-values"
                className={`text-sm font-medium ${
                  hasCustomValues
                    ? "cursor-not-allowed opacity-60"
                    : "cursor-pointer"
                }`}
              >
                Allow custom values
              </Label>
              <HoverCard>
                <HoverCardTrigger asChild>
                  <button type="button" className="focus:outline-none">
                    <AlertTriangle className="h-4 w-4 text-amber-500 cursor-help hover:text-amber-600 transition-colors" />
                  </button>
                </HoverCardTrigger>
                <HoverCardContent className="w-80" align="start">
                  <div className="space-y-2 text-sm">
                    {hasCustomValues ? (
                      <>
                        <p className="font-medium text-amber-600 dark:text-amber-500">
                          Custom values detected.
                        </p>
                        <p className="text-muted-foreground">
                          You cannot disable custom values while custom entries
                          exist. Remove all custom values first to disable this
                          option.
                        </p>
                      </>
                    ) : (
                      <>
                        <p className="text-muted-foreground">
                          Enabling this allows you to enter custom values not in
                          the predefined list.
                        </p>
                        <p className="font-medium text-amber-600 dark:text-amber-500">
                          Warning:
                        </p>
                        <p className="text-muted-foreground">
                          Custom values may cause validation errors or
                          unexpected behavior if they don&apos;t match FHIR
                          specifications.
                        </p>
                      </>
                    )}
                  </div>
                </HoverCardContent>
              </HoverCard>
            </div>
          </div>

          {/* Add from Data Paths button */}
          {dataFormat && dataFolderPath && (
            <Button
              onClick={() => setIsExtractDialogOpen(true)}
              variant="outline"
              size="sm"
              className="flex items-center gap-2 shrink-0"
            >
              <FileSearch className="h-4 w-4" />
              <span className="hidden sm:inline">Extract from Data</span>
              <span className="sm:hidden">Extract</span>
            </Button>
          )}
        </div>
      </div>

      {/* Data Path Selection Dialog */}
      <ExtractValuesDialog
        isOpen={isExtractDialogOpen}
        onOpenChange={setIsExtractDialogOpen}
        onExtract={handleExtractedValues}
        existingUserValues={existingUserValues}
      />

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
          <VisualEditorComponent
            title={config.title}
            mappings={mappings}
            addMapping={addMapping}
            updateMapping={updateMapping}
            removeMapping={removeMapping}
            availableOptions={availableOptions}
            allowCustomValues={allowCustomValues}
          />
        </TabsContent>

        {/* Manual JSON Tab */}
        <TabsContent value="manual" className="flex-1 flex flex-col min-h-0">
          <ManualEditorComponent
            currentMappings={mappings}
            availableOptions={availableOptions}
            onChange={handleManualJsonChange}
            allowCustomValues={allowCustomValues}
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
