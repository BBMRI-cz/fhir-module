import { useState, useContext } from "react";
import { AlertTriangle, FileSearch, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DataField } from "@/types/actions/configuration-details/types";
import { SetupWizardContext } from "@/context/SetupWizardContext";
import {
  extractValuesFromPaths,
  PathExtractionOptions,
} from "@/actions/folder/extract-values-from-path";

interface ExtractValuesDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onExtract: (values: string[]) => void;
  existingUserValues: Set<string>;
}

export default function ExtractValuesDialog({
  isOpen,
  onOpenChange,
  onExtract,
  existingUserValues,
}: ExtractValuesDialogProps) {
  const { dataFields, dataFormat, dataFolderPath, csvSeparator } =
    useContext(SetupWizardContext);

  const [selectedPaths, setSelectedPaths] = useState<PathExtractionOptions[]>(
    []
  );
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionWarning, setExtractionWarning] = useState<string | null>(
    null
  );
  const [extractionError, setExtractionError] = useState<string | null>(null);

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      // Reset state when closing
      setSelectedPaths([]);
      setExtractionWarning(null);
      setExtractionError(null);
    }
    onOpenChange(open);
  };

  const handleAddPath = (path: string) => {
    if (path && !selectedPaths.some((p) => p.path === path)) {
      setSelectedPaths((prev) => [
        ...prev,
        {
          path,
          findAnywhere: false,
          iterateSubelements: false,
          selectedAttribute: undefined,
        },
      ]);
    }
  };

  const handleRemovePath = (path: string) => {
    setSelectedPaths((prev) => prev.filter((p) => p.path !== path));
  };

  const handleUpdatePathOption = (
    path: string,
    updates: Partial<PathExtractionOptions>
  ) => {
    setSelectedPaths((prev) =>
      prev.map((p) => (p.path === path ? { ...p, ...updates } : p))
    );
  };

  const handleConfirmExtraction = async () => {
    if (selectedPaths.length === 0 || !dataFolderPath || !dataFormat) return;

    setIsExtracting(true);
    setExtractionError(null);
    setExtractionWarning(null);

    try {
      const result = await extractValuesFromPaths(
        dataFolderPath,
        selectedPaths,
        dataFormat,
        csvSeparator
      );

      if (!result.success) {
        setExtractionError(result.message);
        setIsExtracting(false);
        return;
      }

      if (result.warning) {
        setExtractionWarning(result.warning);
      }

      const extractedValues = result.values || [];

      // Filter out values that already exist in mappings
      const newValues = extractedValues.filter(
        (val) => !existingUserValues.has(val)
      );

      if (newValues.length === 0) {
        setExtractionError(
          "No new unique values found. All extracted values already exist in the mappings."
        );
        setIsExtracting(false);
        return;
      }

      // Call the onExtract callback with the new values
      onExtract(newValues);
      handleOpenChange(false);
    } catch (err) {
      setExtractionError(
        err instanceof Error ? err.message : "Failed to extract values"
      );
    } finally {
      setIsExtracting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileSearch className="h-5 w-5" />
            Extract Values from Data
          </DialogTitle>
          <DialogDescription>
            Select one or more data paths. Values from these paths will be
            extracted from all {dataFormat?.toUpperCase()} files and added as
            mappings.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex flex-col gap-4 py-4">
          {/* Warning message for too many files */}
          {extractionWarning && (
            <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
              <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
              <p className="text-sm text-amber-700 dark:text-amber-400">
                {extractionWarning}
              </p>
            </div>
          )}

          {/* Error message */}
          {extractionError && (
            <div className="flex items-start gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
              <AlertTriangle className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
              <p className="text-sm text-red-700 dark:text-red-400">
                {extractionError}
              </p>
            </div>
          )}

          {/* Path Selection */}
          <div className="flex-1 space-y-3 min-h-0 overflow-y-auto">
            {/* Selected Paths Display */}
            {selectedPaths.length > 0 && (
              <div className="space-y-2">
                <Label className="text-sm font-medium">
                  Selected Paths ({selectedPaths.length})
                </Label>
                <div className="space-y-2 max-h-[250px] overflow-y-auto">
                  {selectedPaths.map((pathOpt) => {
                    const field = dataFields.find(
                      (f) => f.path === pathOpt.path
                    );
                    const hasAttributes =
                      (field?.attributes?.length ?? 0) > 0;

                    return (
                      <div
                        key={pathOpt.path}
                        className="p-3 border rounded-lg bg-muted/30 space-y-2"
                      >
                        {/* Path header with remove button */}
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">
                              {field?.name || pathOpt.path}
                            </p>
                            <p className="text-xs text-muted-foreground truncate">
                              {pathOpt.path}
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleRemovePath(pathOpt.path)}
                            disabled={isExtracting}
                            className="hover:bg-destructive/20 rounded p-1 transition-colors text-destructive"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>

                        {/* XML-specific options */}
                        {dataFormat === "xml" && (
                          <div className="flex flex-wrap gap-x-4 gap-y-2 pt-2 border-t">
                            <div className="flex items-center gap-2">
                              <Checkbox
                                id={`find-anywhere-${pathOpt.path}`}
                                checked={pathOpt.findAnywhere ?? false}
                                disabled={
                                  isExtracting || !!pathOpt.selectedAttribute
                                }
                                onCheckedChange={(checked) =>
                                  handleUpdatePathOption(pathOpt.path, {
                                    findAnywhere: checked as boolean,
                                  })
                                }
                              />
                              <Label
                                htmlFor={`find-anywhere-${pathOpt.path}`}
                                className="text-xs"
                              >
                                Search everywhere
                              </Label>
                            </div>

                            <div className="flex items-center gap-2">
                              <Checkbox
                                id={`iterate-sub-${pathOpt.path}`}
                                checked={pathOpt.iterateSubelements ?? false}
                                disabled={
                                  isExtracting || !!pathOpt.selectedAttribute
                                }
                                onCheckedChange={(checked) =>
                                  handleUpdatePathOption(pathOpt.path, {
                                    iterateSubelements: checked as boolean,
                                  })
                                }
                              />
                              <Label
                                htmlFor={`iterate-sub-${pathOpt.path}`}
                                className="text-xs"
                              >
                                Iterate sub-elements
                              </Label>
                            </div>

                            {hasAttributes && (
                              <div className="flex items-center gap-2 w-full sm:w-auto flex-wrap">
                                <div className="flex items-center gap-2">
                                  <Checkbox
                                    id={`use-attr-${pathOpt.path}`}
                                    checked={
                                      pathOpt.selectedAttribute !== undefined
                                    }
                                    disabled={
                                      isExtracting ||
                                      pathOpt.findAnywhere ||
                                      pathOpt.iterateSubelements
                                    }
                                    onCheckedChange={(checked) => {
                                      if (checked) {
                                        handleUpdatePathOption(pathOpt.path, {
                                          selectedAttribute: "",
                                        });
                                      } else {
                                        handleUpdatePathOption(pathOpt.path, {
                                          selectedAttribute: undefined,
                                        });
                                      }
                                    }}
                                  />
                                  <Label
                                    htmlFor={`use-attr-${pathOpt.path}`}
                                    className="text-xs"
                                  >
                                    Use attribute
                                  </Label>
                                </div>
                                {pathOpt.selectedAttribute !== undefined && (
                                  <Select
                                    value={pathOpt.selectedAttribute || ""}
                                    onValueChange={(value) =>
                                      handleUpdatePathOption(pathOpt.path, {
                                        selectedAttribute: value || undefined,
                                      })
                                    }
                                    disabled={isExtracting}
                                  >
                                    <SelectTrigger className="h-7 w-[140px] text-xs">
                                      <SelectValue placeholder="Select attribute..." />
                                    </SelectTrigger>
                                    <SelectContent>
                                      {field?.attributes?.map((attr) => (
                                        <SelectItem
                                          key={attr}
                                          value={attr}
                                          className="text-xs"
                                        >
                                          {attr}
                                        </SelectItem>
                                      ))}
                                    </SelectContent>
                                  </Select>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Add Path Dropdown */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Add Data Path</Label>
              <Select
                value=""
                onValueChange={handleAddPath}
                disabled={isExtracting}
              >
                <SelectTrigger className="w-full h-9 text-xs sm:text-sm">
                  <SelectValue placeholder="Select a data field to add..." />
                </SelectTrigger>
                <SelectContent className="w-[var(--radix-select-trigger-width)] text-xs sm:text-sm">
                  {(dataFields as DataField[])
                    .sort((a, b) => a.path.localeCompare(b.path))
                    .filter(
                      (field) =>
                        !selectedPaths.some((p) => p.path === field.path)
                    )
                    .map((field) => (
                      <SelectItem
                        key={field.path}
                        value={field.path}
                        className="py-2 md:py-3"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center w-full gap-1 sm:gap-2">
                          <span className="text-xs sm:text-sm truncate">
                            {field.name}
                          </span>
                          <span className="text-xs text-gray-500 truncate">
                            {field.path}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
              {dataFields.length === 0 && (
                <p className="text-xs text-muted-foreground">
                  No data paths available. Please ensure you have selected a
                  data folder with {dataFormat?.toUpperCase()} files.
                </p>
              )}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={isExtracting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleConfirmExtraction}
            disabled={selectedPaths.length === 0 || isExtracting}
          >
            {isExtracting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Extracting...
              </>
            ) : (
              <>
                Extract Values
                {selectedPaths.length > 0 &&
                  ` (${selectedPaths.length} path${
                    selectedPaths.length === 1 ? "" : "s"
                  })`}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

