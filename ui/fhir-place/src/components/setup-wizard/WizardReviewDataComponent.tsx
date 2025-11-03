"use client";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { SetupWizardContext } from "@/context/SetupWizardContext";
import { useContext, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  FileText,
  Files,
  ArrowLeft,
  ArrowRight,
  CheckCircle,
  FolderOpen,
} from "lucide-react";
import { getFormatIcon } from "@/lib/format-utils";
import { parseDataFromFolder } from "@/actions/configuration-details/configuration-details-actions";

export default function WizardReviewDataComponent() {
  const {
    dataFolderPath,
    dataFormat,
    dataFiles,
    nextStep,
    previousStep,
    setDataFields,
    csvSeparator,
  } = useContext(SetupWizardContext);

  useEffect(() => {
    async function fetchData() {
      const data = await parseDataFromFolder(
        dataFolderPath,
        dataFormat === "csv" ? csvSeparator : undefined
      );
      setDataFields(data.fields || []);
    }
    fetchData();
  }, [dataFolderPath, csvSeparator, dataFormat, setDataFields]);

  const canContinue = dataFiles.length > 0;

  return (
    <div className="h-full w-full bg-gradient-to-br flex flex-col">
      <div className="mx-auto w-full h-full flex flex-col flex-1 min-h-0">
        <Card className="border-0 shadow-xl backdrop-blur-sm flex-1 flex flex-col min-h-0">
          <CardHeader className="pb-3 flex-shrink-0">
            <CardTitle className="text-xl font-semibold flex items-center gap-2">
              <Files className="w-5 h-5" />
              Review Data Files
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 flex-1 overflow-y-auto overflow-x-hidden min-h-0">
            {/* Summary Information */}
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <div className="grid gap-4 md:grid-cols-2 overflow-x-hidden">
                <div>
                  <h3 className="text-sm font-semibold text-blue-800 dark:text-blue-200 mb-2">
                    Selected Folder
                  </h3>
                  <div className="flex items-center gap-2">
                    <FolderOpen className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    <div className="text-xs font-mono text-blue-700 dark:text-blue-300 truncate">
                      {dataFolderPath}
                    </div>
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-blue-800 dark:text-blue-200 mb-2">
                    Data Format
                  </h3>
                  <div className="flex items-center gap-2">
                    {dataFormat && getFormatIcon(dataFormat)}
                    <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                      {dataFormat?.toUpperCase()} Files
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Files List */}
            <div className="space-y-3 overflow-auto">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  Found Files ({dataFiles.length})
                </h3>
              </div>

              {dataFiles.length > 0 ? (
                <div className="border rounded-lg p-4">
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {dataFiles.map((file) => (
                      <div
                        key={file}
                        className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border"
                      >
                        <div className="flex-shrink-0">
                          {dataFormat && getFormatIcon(dataFormat)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                            {file}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {dataFormat?.toUpperCase()} file
                          </p>
                        </div>
                        <div className="flex-shrink-0">
                          <div
                            className="w-2 h-2 bg-green-500 rounded-full"
                            title="Ready for processing"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center p-8 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                    No files found
                  </h4>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Please go back and select a folder with {dataFormat} files.
                  </p>
                </div>
              )}
            </div>
          </CardContent>
          <CardFooter className="flex justify-between items-center pt-4 flex-shrink-0">
            <Button
              variant="outline"
              onClick={() => previousStep()}
              size="sm"
              className="flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </Button>
            <Button
              onClick={() => nextStep()}
              disabled={!canContinue}
              size="sm"
            >
              Continue
              <ArrowRight className="w-3 h-3" />
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
