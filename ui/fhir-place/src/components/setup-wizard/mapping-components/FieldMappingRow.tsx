import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { useCallback, useContext, useState } from "react";
import { SetupWizardContext } from "@/context/SetupWizardContext";
import { MappingContext } from "@/context/MappingContext";
import FieldMappingRowRecord from "@/components/setup-wizard/mapping-components/FieldMappingRowRecord";
import { DataMappingRecord } from "@/types/setup-wizard/types";
import { DataField } from "@/types/actions/configuration-details/types";

interface FieldMappingRowProps {
  fhirField: string;
}

export function FieldMappingRow({ fhirField }: FieldMappingRowProps) {
  const [usedPaths, setUsedPaths] = useState<string[]>([]);

  const { dataFields, dataFormat } = useContext(SetupWizardContext);
  const { data, addRecord, deleteRecord } = useContext(MappingContext);

  const currentField = data[fhirField];

  const currentMappings = currentField.mappings;
  const isRequired = currentField.isRequired;
  const hasRequiredError = isRequired && currentMappings.length === 0;

  const handleValueChange = useCallback(
    (pathValue: string) => {
      setUsedPaths((prevUsedPaths) => [...prevUsedPaths, pathValue]);

      addRecord(fhirField, pathValue);
    },
    [fhirField, addRecord]
  );

  const handleDelete = useCallback(
    (index: number) => {
      const valueToRemove = currentField.mappings[index].value;

      setUsedPaths((prevUsedPaths) =>
        prevUsedPaths.filter((f) => f !== valueToRemove)
      );

      deleteRecord(fhirField, index);
    },
    [fhirField, deleteRecord, currentField.mappings]
  );

  return (
    <div
      className={`p-3 md:p-4 border rounded-lg ${
        hasRequiredError ? "border-red-400" : ""
      }`}
    >
      {/* Field Header */}
      <div className="mb-2 md:mb-3">
        <Label className="text-xs sm:text-sm font-medium break-all">
          FHIR Field:{" "}
          <code className="px-1 rounded text-xs sm:text-sm">{fhirField}</code>
          {isRequired && (
            <>
              <span className="text-red-500 ml-1">*</span>
              <span className="text-red-500 font-medium text-xs sm:text-sm">
                {" "}
                (Required)
              </span>
            </>
          )}
        </Label>
      </div>

      <div className="flex gap-2">
        <div className="flex-1 min-w-0">
          <div className="space-y-2">
            {/* Existing Mapped Fields */}
            {currentMappings.length > 0 && (
              <div className="space-y-2">
                {currentMappings.map((_: DataMappingRecord, index: number) => (
                  <FieldMappingRowRecord
                    key={index} // NOSONAR
                    fhirField={fhirField}
                    index={index}
                    handleDelete={handleDelete}
                  />
                ))}
              </div>
            )}

            {/* Add New Field Dropdown */}
            {(dataFormat === "xml" || currentMappings.length === 0) && (
              <Select value="" onValueChange={handleValueChange}>
                <SelectTrigger className="w-full h-9 text-xs sm:text-sm">
                  <SelectValue placeholder="Add data field..." />
                </SelectTrigger>
                <SelectContent className="w-[var(--radix-select-trigger-width)] text-xs sm:text-sm">
                  {(dataFields as DataField[])
                    .sort((a, b) => a.path.localeCompare(b.path))
                    .filter((field) => !usedPaths.includes(field.path))
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
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
