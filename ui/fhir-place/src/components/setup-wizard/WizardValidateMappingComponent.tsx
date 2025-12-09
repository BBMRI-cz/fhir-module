"use client";

/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useContext, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { SetupWizardContext } from "@/context/SetupWizardContext";
import { validateMappings } from "@/actions/setup-wizard/validateMappings";
import {
  AlertCircle,
  User,
  Activity,
  TestTube,
  ChevronRight,
  AlertTriangle,
  Clock,
  Info,
} from "lucide-react";
import { Tooltip } from "@/components/ui/tooltip";
import { ValidationResult } from "@/types/setup-wizard/types";

type SelectedErrorType = {
  error: string;
  category: string;
  icon: React.ReactNode;
};

type ErrorCategory = "general" | "donor" | "condition" | "sample";

type ColorVariant = {
  border: string;
  background: string;
  text: string;
  icon: string;
  badge: string;
};

const COLOR_VARIANTS: Record<ErrorCategory, ColorVariant> = {
  general: {
    border: "border-l-yellow-500",
    background: "bg-yellow-50",
    text: "text-yellow-700",
    icon: "text-yellow-500",
    badge: "bg-yellow-100 text-yellow-700",
  },
  donor: {
    border: "border-l-red-500",
    background: "bg-red-50",
    text: "text-red-700",
    icon: "text-red-500",
    badge: "bg-red-100 text-red-700",
  },
  condition: {
    border: "border-l-orange-500",
    background: "bg-orange-50",
    text: "text-orange-700",
    icon: "text-orange-500",
    badge: "bg-orange-100 text-orange-700",
  },
  sample: {
    border: "border-l-blue-500",
    background: "bg-blue-50",
    text: "text-blue-700",
    icon: "text-blue-500",
    badge: "bg-blue-100 text-blue-700",
  },
};

const getErrorSummary = (error: string): string => {
  const firstSentence = error.split(".")[0];
  if (firstSentence.length <= 80) {
    return firstSentence + (error.includes(".") ? "..." : "");
  }
  return error.substring(0, 80) + "...";
};

function ValidationStatus({
  validationResult,
}: {
  validationResult: ValidationResult | null;
}) {
  if (!validationResult) return null;

  return (
    <div className="flex items-center gap-2 sm:gap-3">
      {validationResult.success ? (
        <>
          <div className="h-2.5 w-2.5 sm:h-3 sm:w-3 bg-green-500 rounded-full"></div>
          <span className="text-green-600 font-medium text-xs sm:text-sm md:text-base">
            Mappings are valid!
          </span>
        </>
      ) : (
        <>
          <div className="h-2.5 w-2.5 sm:h-3 sm:w-3 bg-red-500 rounded-full"></div>
          <span className="text-red-600 font-medium text-xs sm:text-sm md:text-base">
            Mappings contain errors
          </span>
        </>
      )}
    </div>
  );
}

export default function WizardValidateMappingComponent() {
  const {
    nextStep,
    previousStep,
    wizardState,
    dataFormat,
    dataFolderPath,
    csvSeparator,
  } = useContext(SetupWizardContext);

  const [blazeValidationResult, setBlazeValidationResult] =
    useState<ValidationResult | null>(null);
  const [miabisValidationResult, setMiabisValidationResult] =
    useState<ValidationResult | null>(null);
  const [selectedError, setSelectedError] = useState<SelectedErrorType | null>(
    null
  );
  const [validateAllFiles, setValidateAllFiles] = useState(false);
  const [skipValidation, setSkipValidation] = useState(false);
  const [isValidatingBlaze, setIsValidatingBlaze] = useState(false);
  const [isValidatingMiabis, setIsValidatingMiabis] = useState(false);

  const { syncTarget } = wizardState;
  const showBlazeButton = syncTarget === "blaze" || syncTarget === "both";
  const showMiabisButton = syncTarget === "miabis" || syncTarget === "both";

  const initiateCheckBlaze = async () => {
    setIsValidatingBlaze(true);
    try {
      const result = await validateMappings(
        wizardState,
        dataFormat!,
        dataFolderPath!,
        "blaze",
        csvSeparator,
        validateAllFiles
      );
      setBlazeValidationResult(result);
    } finally {
      setIsValidatingBlaze(false);
    }
  };

  const initiateCheckMiabis = async () => {
    setIsValidatingMiabis(true);
    try {
      // Create a temporary wizardState with only MIABIS config
      const miabisOnlyState = {
        ...wizardState,
        syncTarget: "miabis" as const,
      };
      const result = await validateMappings(
        miabisOnlyState,
        dataFormat!,
        dataFolderPath!,
        "miabis",
        csvSeparator,
        validateAllFiles
      );
      setMiabisValidationResult(result);
    } finally {
      setIsValidatingMiabis(false);
    }
  };

  const getBlazeValidationButtonLabel = () => {
    if (!isValidatingBlaze) {
      return syncTarget === "both"
        ? "Validate BLAZE"
        : "Check mappings validity";
    }
    return validateAllFiles ? "Validating all files..." : "Validating...";
  };

  const getMiabisValidationButtonLabel = () => {
    if (!isValidatingMiabis) {
      return syncTarget === "both"
        ? "Validate MIABIS"
        : "Check mappings validity";
    }
    return validateAllFiles ? "Validating all files..." : "Validating...";
  };

  // Determine if user can continue
  const canContinue = () => {
    if (skipValidation) {
      return true;
    }
    if (syncTarget === "both") {
      return blazeValidationResult?.success && miabisValidationResult?.success;
    } else if (syncTarget === "blaze") {
      return blazeValidationResult?.success;
    } else if (syncTarget === "miabis") {
      return miabisValidationResult?.success;
    }
    return false;
  };

  // Combined validation result for display
  const displayValidationResult = () => {
    if (syncTarget === "both") {
      // Show both results or the first error
      if (!blazeValidationResult && !miabisValidationResult) return null;
      if (blazeValidationResult && !blazeValidationResult.success)
        return blazeValidationResult;
      if (miabisValidationResult && !miabisValidationResult.success)
        return miabisValidationResult;
      if (blazeValidationResult?.success && miabisValidationResult?.success)
        return blazeValidationResult;
      return null;
    } else if (syncTarget === "blaze") {
      return blazeValidationResult;
    } else if (syncTarget === "miabis") {
      return miabisValidationResult;
    }
    return null;
  };

  return (
    <div className="h-full w-full bg-gradient-to-br">
      <Card className="border-0 shadow-xl h-full w-full gap-2">
        <CardHeader className="flex-shrink-0">
          <div className="flex items-center gap-2">
            <CardTitle className="text-base lg:text-2xl font-semibold flex items-center">
              Test your mappings
            </CardTitle>
            {/* Info icon for smaller screens - shows tooltip on hover/click */}
            <Tooltip
              content="Two-stage validation: Stage 1 validates structure in all files (fast). Stage 2 validates data parsing."
              className="max-w-xs text-left"
            >
              <Info className="h-4 w-4 text-muted-foreground lg:hidden cursor-help" />
            </Tooltip>
          </div>
          <p className="text-muted-foreground text-xs sm:text-sm leading-tight sm:leading-normal">
            Validate your data mappings to ensure they work correctly with your
            data files.
          </p>

          {/* Info and Options Row */}
          <div className="flex flex-col lg:flex-row gap-2 sm:gap-3">
            {/* Info Section - Two-stage validation - Hidden on smaller screens */}
            <div className="hidden lg:flex flex-1 rounded-md border bg-muted/30 p-3">
              <div className="flex items-start gap-2.5">
                <Info className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                <div className="flex-1 space-y-1.5">
                  <h4 className="text-sm font-semibold">
                    Two-stage validation process
                  </h4>
                  <div className="space-y-1 text-sm text-muted-foreground">
                    <div className="flex gap-1.5">
                      <span className="font-medium">Stage 1:</span>
                      <span>Validates structure in all files (fast)</span>
                    </div>
                    <div className="flex gap-1.5">
                      <span className="font-medium">Stage 2:</span>
                      <span>Validates data parsing</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Validate All Files Option */}
            <div className="flex-1 rounded-md border bg-muted/30 p-2 sm:p-3">
              <div className="flex items-start gap-2 sm:gap-3">
                <Checkbox
                  id="validateAllFiles"
                  checked={validateAllFiles}
                  onCheckedChange={(checked) =>
                    setValidateAllFiles(checked as boolean)
                  }
                  className="flex-shrink-0"
                />
                <div className="flex-1 min-w-0 space-y-0.5 sm:space-y-1">
                  <label
                    htmlFor="validateAllFiles"
                    className="text-xs sm:text-sm font-medium cursor-pointer flex items-center gap-1 sm:gap-1.5"
                  >
                    <span className="hidden md:inline">
                      Validate all files in folder
                    </span>
                    <span className="md:hidden">Validate all files</span>
                    <Clock className="h-3 w-3 sm:h-4 sm:w-4 text-muted-foreground flex-shrink-0" />
                  </label>
                  <p className="text-xs text-muted-foreground leading-tight">
                    <span className="hidden lg:inline">
                      By default, only the first file is validated in Stage 2.{" "}
                    </span>
                    <span className="font-medium text-foreground">
                      <span className="hidden md:inline">
                        Enabling this may take longer with large datasets.
                      </span>
                      <span className="text-xs md:hidden">
                        Slower with large datasets
                      </span>
                    </span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col flex-1 overflow-hidden p-4 sm:p-6 2xl:py-2 sm:py-2">
          {/* Validation Controls Section */}
          <div className="flex flex-col items-center justify-center gap-3">
            {/* Validation Buttons */}
            <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3">
              {showBlazeButton && (
                <Button
                  onClick={initiateCheckBlaze}
                  size="lg"
                  className="h-9 sm:h-10 text-xs lg:text-sm"
                  disabled={isValidatingBlaze || isValidatingMiabis}
                  variant={
                    blazeValidationResult?.success ? "default" : "outline"
                  }
                >
                  {getBlazeValidationButtonLabel()}
                  {blazeValidationResult?.success && (
                    <span className="ml-2">✓</span>
                  )}
                </Button>
              )}
              {showMiabisButton && (
                <Button
                  onClick={initiateCheckMiabis}
                  size="lg"
                  className="h-9 sm:h-10 text-xs lg:text-sm"
                  disabled={isValidatingBlaze || isValidatingMiabis}
                  variant={
                    miabisValidationResult?.success ? "default" : "outline"
                  }
                >
                  {getMiabisValidationButtonLabel()}
                  {miabisValidationResult?.success && (
                    <span className="ml-2">✓</span>
                  )}
                </Button>
              )}
            </div>

            {/* Validation Status - Show combined for both, or individual */}
            {syncTarget === "both" ? (
              <div className="flex flex-col items-center gap-2 w-full">
                {blazeValidationResult && (
                  <div className="flex items-center gap-2 text-xs sm:text-sm">
                    <span className="font-semibold text-muted-foreground">
                      BLAZE:
                    </span>
                    <ValidationStatus
                      validationResult={blazeValidationResult}
                    />
                  </div>
                )}
                {miabisValidationResult && (
                  <div className="flex items-center gap-2 text-xs sm:text-sm">
                    <span className="font-semibold text-muted-foreground">
                      MIABIS:
                    </span>
                    <ValidationStatus
                      validationResult={miabisValidationResult}
                    />
                  </div>
                )}
              </div>
            ) : (
              <ValidationStatus validationResult={displayValidationResult()} />
            )}
          </div>

          {/* Error Details Section - Scrollable */}
          {displayValidationResult() && !displayValidationResult()!.success && (
            <div className="flex-1 overflow-y-auto">
              <ErrorDetailsSection
                validationResult={displayValidationResult()!}
                setSelectedError={setSelectedError}
              />
            </div>
          )}
        </CardContent>
        <CardFooter className="flex justify-between items-center gap-2 p-4 sm:p-6 2xl:py-0 sm:py-0">
          <Button
            onClick={previousStep}
            variant="outline"
            className="h-8 sm:h-10 text-xs sm:text-sm px-2 sm:px-4"
          >
            Back
          </Button>
          <div className="flex items-center gap-3 sm:gap-4">
            <div className="flex items-center gap-2">
              <Checkbox
                id="skipValidation"
                checked={skipValidation}
                onCheckedChange={(checked) =>
                  setSkipValidation(checked as boolean)
                }
                className="border-amber-500 data-[state=checked]:bg-amber-500 data-[state=checked]:border-amber-500"
              />
              <label
                htmlFor="skipValidation"
                className="text-xs sm:text-sm text-amber-600 cursor-pointer flex items-center gap-1"
              >
                <AlertTriangle className="h-3 w-3 sm:h-4 sm:w-4" />
                <span className="hidden sm:inline">Skip validation</span>
                <span className="sm:hidden">Skip</span>
              </label>
            </div>
            <Button
              onClick={nextStep}
              disabled={!canContinue()}
              className="h-8 sm:h-10 text-xs sm:text-sm px-3 sm:px-4"
            >
              Continue
            </Button>
          </div>
        </CardFooter>
      </Card>

      {/* Error Details Dialog */}
      <Dialog
        open={!!selectedError}
        onOpenChange={() => setSelectedError(null)}
      >
        <DialogContent className="max-w-3xl max-h-[100vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base sm:text-lg">
              {selectedError?.icon}
              {selectedError?.category}
            </DialogTitle>
            <DialogDescription className="text-xs sm:text-sm">
              Full error details and information
            </DialogDescription>
          </DialogHeader>
          <div className="bg-muted/50 rounded-lg p-3 sm:p-4 border">
            <p className="text-xs sm:text-sm leading-relaxed whitespace-pre-wrap">
              {selectedError?.error}
            </p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function ErrorDetailsSection({
  validationResult,
  setSelectedError,
}: {
  validationResult: ValidationResult;
  setSelectedError: (error: SelectedErrorType | null) => void;
}) {
  const [selectedErrorList, setSelectedErrorList] = useState<{
    category: string;
    name: string;
    errors: string[];
    icon: React.ReactNode;
    colors: ColorVariant;
  } | null>(null);

  const handleOpenErrorList = (
    category: ErrorCategory,
    name: string,
    errors: string[],
    icon: React.ReactNode
  ) => {
    const colors = COLOR_VARIANTS[category];
    const iconElement = React.isValidElement(icon)
      ? React.cloneElement(icon as React.ReactElement<any>, {
          className: `h-5 w-5 ${colors.icon}`,
        })
      : icon;

    setSelectedErrorList({
      category,
      name,
      errors,
      icon: iconElement,
      colors,
    });
  };

  return (
    <div className="w-full pb-4 sm:pb-8">
      <h3 className="text-sm sm:text-base md:text-lg font-semibold mb-3 sm:mb-6">
        Error Summary
      </h3>

      {/* Error summary grid - compact and responsive */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <ErrorSummaryCard
          category="general"
          name="General"
          errors={validationResult.genericErrors}
          icon={<AlertTriangle className="h-5 w-5" />}
          onOpenErrorList={handleOpenErrorList}
        />

        <ErrorSummaryCard
          category="donor"
          name="Donor"
          errors={validationResult.patientErrors}
          icon={<User className="h-5 w-5" />}
          onOpenErrorList={handleOpenErrorList}
        />

        <ErrorSummaryCard
          category="condition"
          name="Condition"
          errors={validationResult.conditionErrors}
          icon={<Activity className="h-5 w-5" />}
          onOpenErrorList={handleOpenErrorList}
        />

        <ErrorSummaryCard
          category="sample"
          name="Sample"
          errors={validationResult.sampleErrors}
          icon={<TestTube className="h-5 w-5" />}
          onOpenErrorList={handleOpenErrorList}
        />
      </div>

      {/* Error List Dialog */}
      <Dialog
        open={!!selectedErrorList}
        onOpenChange={() => setSelectedErrorList(null)}
      >
        <DialogContent className="max-w-4xl max-h-[80vh] flex flex-col">
          <DialogHeader className="flex-shrink-0">
            <DialogTitle className="flex items-center gap-2 text-base sm:text-lg">
              {selectedErrorList?.icon}
              {selectedErrorList?.name} Errors (
              {selectedErrorList?.errors.length})
            </DialogTitle>
            <DialogDescription className="text-xs sm:text-sm">
              Click on any error below to view its full details.
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto mt-3 sm:mt-4">
            <div className="space-y-2">
              {selectedErrorList?.errors.map((error, index) => (
                <Button
                  key={index} // NOSONAR
                  variant="ghost"
                  className="flex items-start justify-start gap-2 sm:gap-3 p-3 sm:p-4 rounded-lg border hover:bg-muted/50 transition-colors w-full h-auto text-left overflow-x-hidden"
                  onClick={() => {
                    setSelectedError({
                      error,
                      category: `${selectedErrorList.name} Error`,
                      icon: selectedErrorList.icon,
                    });
                    setSelectedErrorList(null);
                  }}
                >
                  <AlertCircle
                    className={`h-3.5 w-3.5 sm:h-4 sm:w-4 ${selectedErrorList?.colors.icon} mt-0.5 flex-shrink-0`}
                  />
                  <span className="text-xs sm:text-sm leading-relaxed flex-1 break-words">
                    {getErrorSummary(error)}
                  </span>
                  <ChevronRight className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-muted-foreground flex-shrink-0" />
                </Button>
              ))}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function ErrorSummaryCard({
  category,
  name,
  errors,
  icon,
  onOpenErrorList,
}: {
  category: ErrorCategory;
  name: string;
  errors: string[] | undefined;
  icon: React.ReactNode;
  onOpenErrorList: (
    category: ErrorCategory,
    name: string,
    errors: string[],
    icon: React.ReactNode
  ) => void;
}) {
  const colors = COLOR_VARIANTS[category];
  const hasErrors = errors && errors.length > 0;

  const handleClick = () => {
    if (hasErrors) {
      onOpenErrorList(category, name, errors, icon);
    }
  };

  let errorText: string;
  if (hasErrors) {
    const errorWord = errors.length > 1 ? "errors" : "error";
    errorText = `${errors.length} ${errorWord}`;
  } else {
    errorText = "No errors";
  }

  return (
    <Card
      className={`border-l-4 transition-all duration-200 ${
        hasErrors
          ? `${colors.border} hover:shadow-md cursor-pointer`
          : "border-l-green-500"
      }`}
      onClick={handleClick}
    >
      <CardContent>
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 sm:gap-3 min-w-0">
            {React.isValidElement(icon)
              ? React.cloneElement(icon as React.ReactElement<any>, {
                  className: `h-5 w-5 sm:h-6 sm:w-6 flex-shrink-0 ${
                    hasErrors ? colors.icon : "text-green-600"
                  }`,
                })
              : icon}
            <div className="min-w-0">
              <h4 className="font-semibold text-xs sm:text-sm md:text-base truncate">
                {name}
              </h4>
              <p className="text-[10px] sm:text-xs md:text-sm text-muted-foreground">
                {errorText}
              </p>
            </div>
          </div>

          {hasErrors ? (
            <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
              <span
                className={`${colors.badge} text-[10px] sm:text-xs md:text-sm px-1.5 sm:px-2 md:px-3 py-0.5 sm:py-1 rounded-full font-medium`}
              >
                {errors.length}
              </span>
              <ChevronRight className="h-3.5 w-3.5 sm:h-4 sm:w-4 md:h-5 md:w-5 text-muted-foreground" />
            </div>
          ) : (
            <div className="h-2.5 w-2.5 sm:h-3 sm:w-3 bg-green-500 rounded-full flex-shrink-0"></div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
