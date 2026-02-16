"use client";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useContext, useState } from "react";
import { Button } from "@/components/ui/button";
import SelectFolderDialog from "@/components/setup-wizard/SelectFolderDialog";
import { FolderOpen, CheckCircle, ArrowRight, FileText } from "lucide-react";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { getFormatIcon } from "@/lib/format-utils";
import { DataFormats, SetupWizardContext } from "@/context/SetupWizardContext";
import { DataFormat } from "@/types/context/setup-wizard-context/types";

export default function WizardSelectDataFolderComponent() {
  const {
    dataFolderPath,
    setDataFolderPath,
    dataFormat,
    setDataFormat,
    csvSeparator,
    setCsvSeparator,
    nextStep,
    dataFiles,
  } = useContext(SetupWizardContext);
  const [isOpen, setIsOpen] = useState(false);

  const canContinue = dataFolderPath && dataFormat && dataFiles.length > 0;

  return (
    <div className="bg-gradient-to-br 2xl:p-4 w-full h-full">
      <Card className="w-full h-full border-0 shadow-xl backdrop-blur-sm flex-1 flex flex-col">
        <CardHeader className="pb-3">
          <CardTitle className="text-xl font-semibold flex items-center gap-2">
            <FolderOpen className="w-5 h-5" />
            Data Folder & Format Selection
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 flex-1 overflow-y-auto">
          <div className="grid gap-4 lg:grid-cols-2">
            {/* Data Folder Selection */}
            <div className="space-y-3">
              <h3 className="text-base font-semibold flex items-center gap-2">
                <FolderOpen className="w-4 h-4" />
                Data Folder
              </h3>
              {dataFolderPath ? (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                    <CheckCircle className="w-3 h-3" />
                    <span className="text-xs font-medium">Folder Selected</span>
                  </div>
                  <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded p-2">
                    <p className="text-xs font-medium text-green-800 dark:text-green-200 mb-1">
                      Selected Folder:
                    </p>
                    <p className="text-xs text-green-700 dark:text-green-300 font-mono break-all bg-white dark:bg-green-900/30 px-2 py-1 rounded border">
                      {dataFolderPath}
                    </p>
                  </div>
                  <SelectFolderDialog
                    isOpen={isOpen}
                    onOpenChange={setIsOpen}
                    onConfirm={setDataFolderPath}
                  >
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setIsOpen(true)}
                      className="flex items-center gap-1"
                    >
                      <FolderOpen className="w-3 h-3" />
                      Change Folder
                    </Button>
                  </SelectFolderDialog>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center border-2 border-dashed rounded p-4 text-center">
                  <FolderOpen className="w-8 h-8 mx-auto mb-2" />
                  <h4 className="text-xs font-medium mb-1">
                    No folder selected
                  </h4>
                  <p className="text-xs mb-3">
                    Choose a folder containing your data files
                  </p>
                  <SelectFolderDialog
                    isOpen={isOpen}
                    onOpenChange={setIsOpen}
                    onConfirm={setDataFolderPath}
                  >
                    <Button
                      size="sm"
                      onClick={() => setIsOpen(true)}
                      className="flex items-center gap-1"
                    >
                      <FolderOpen className="w-3 h-3" />
                      Select Folder
                    </Button>
                  </SelectFolderDialog>
                </div>
              )}
            </div>

            {/* Data Format Selection */}
            <div className="space-y-3">
              <h3 className="text-base font-semibold flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Data Format
              </h3>

              <div className="space-y-2">
                <RadioGroup
                  value={dataFormat || ""}
                  onValueChange={(value) => setDataFormat(value as DataFormat)}
                  disabled={!dataFolderPath}
                >
                  {DataFormats.map((format) => (
                    <div
                      key={format.value}
                      className={`flex items-center space-x-2 p-2 border rounded transition-colors ${
                        dataFormat === format.value
                          ? "bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800"
                          : ""
                      }`}
                    >
                      <RadioGroupItem value={format.value} id={format.value} />
                      <div className="flex items-center gap-2 flex-1">
                        {getFormatIcon(format.value, "w-5 h-5")}
                        <div className="flex-1">
                          <Label
                            htmlFor={format.value}
                            className="text-xs font-medium cursor-pointer"
                          >
                            {format.label}
                          </Label>
                          <p className="text-xs text-gray-600 dark:text-gray-300">
                            {format.description}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </RadioGroup>

                {/* CSV Separator Input */}
                {dataFormat === "csv" && (
                  <div className="mt-3 p-3 border rounded bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
                    <Label
                      htmlFor="csv-separator"
                      className="text-xs font-medium mb-1 block"
                    >
                      CSV Separator
                    </Label>
                    <Input
                      id="csv-separator"
                      type="text"
                      value={csvSeparator}
                      onChange={(e) => setCsvSeparator(e.target.value)}
                      placeholder="Enter separator (e.g., , or ; or |)"
                      className="text-xs h-8"
                      maxLength={3}
                    />
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      Common separators: comma (,), semicolon (;), tab (\t),
                      pipe (|)
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Data Files Summary */}
          {dataFolderPath && dataFormat && dataFiles.length > 0 && (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded p-3">
              <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm font-medium">
                  {dataFiles.length} {dataFormat.toUpperCase()} file
                  {dataFiles.length !== 1 && "s"} found and ready for review
                </span>
              </div>
            </div>
          )}

          {/* No Files Found Warning */}
          {dataFolderPath && dataFormat && dataFiles.length === 0 && (
            <div className="space-y-2">
              <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded p-2">
                <div className="flex items-center gap-1 text-amber-600 dark:text-amber-400 mb-1">
                  <FileText className="w-3 h-3" />
                  <span className="text-xs font-medium">
                    No {dataFormat.toUpperCase()} files found
                  </span>
                </div>
                <p className="text-xs text-amber-700 dark:text-amber-300">
                  The selected folder doesn&apos;t contain any .{dataFormat}{" "}
                  files. Please select a different folder or format.
                </p>
              </div>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button onClick={() => nextStep()} disabled={!canContinue} size="sm">
            Continue
            <ArrowRight className="w-3 h-3" />
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
