import { useContext } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SetupWizardContext } from "@/context/SetupWizardContext";

interface FieldControlsProps {
  fhirField: string;
  fieldIndex: number;
  availableAttributes: string[];
  isSearchWholeRecordEnabled: boolean;
  isIterateSubelementsEnabled: boolean;
  isAttributeEnabled: boolean;
  currentAttribute: string;
  onSearchWholeRecordChange: (
    fhirField: string,
    fieldIndex: number,
    enabled: boolean
  ) => void;
  onIterateSubelementsChange: (
    fhirField: string,
    fieldIndex: number,
    enabled: boolean
  ) => void;
  onAttributeEnabledChange: (
    fhirField: string,
    fieldIndex: number,
    enabled: boolean
  ) => void;
  onAttributeChange: (
    fhirField: string,
    fieldIndex: number,
    attributeName: string
  ) => void;
}

export function FieldControls({
  fhirField,
  fieldIndex,
  availableAttributes,
  isSearchWholeRecordEnabled,
  isIterateSubelementsEnabled,
  isAttributeEnabled,
  currentAttribute,
  onSearchWholeRecordChange,
  onIterateSubelementsChange,
  onAttributeEnabledChange,
  onAttributeChange,
}: FieldControlsProps) {
  const { dataFormat } = useContext(SetupWizardContext);

  return (
    <div className="flex flex-wrap gap-4 text-xs">
      {/* Search whole record checkbox */}
      <div className="flex items-center space-x-2">
        <Checkbox
          checked={isSearchWholeRecordEnabled}
          disabled={isAttributeEnabled}
          onCheckedChange={(checked) => {
            onSearchWholeRecordChange(
              fhirField,
              fieldIndex,
              checked as boolean
            );
          }}
        />
        <span
          className={`text-xs ${isAttributeEnabled ? "text-gray-800" : ""}`}
        >
          Search whole record
        </span>
      </div>

      {/* Iterate subelements checkbox */}
      <div className="flex items-center space-x-2">
        <Checkbox
          checked={isIterateSubelementsEnabled}
          disabled={isAttributeEnabled}
          onCheckedChange={(checked) => {
            onIterateSubelementsChange(
              fhirField,
              fieldIndex,
              checked as boolean
            );
          }}
        />
        <span
          className={`text-xs ${isAttributeEnabled ? "text-gray-800" : ""}`}
        >
          Iterate subelements
        </span>
      </div>

      {/* Attribute selection (XML only) */}
      {dataFormat === "xml" && availableAttributes.length > 0 && (
        <div className="flex items-center space-x-2">
          <Checkbox
            checked={isAttributeEnabled}
            disabled={isSearchWholeRecordEnabled || isIterateSubelementsEnabled}
            onCheckedChange={(checked) => {
              onAttributeEnabledChange(
                fhirField,
                fieldIndex,
                checked as boolean
              );
            }}
          />
          <span
            className={`text-xs ${
              isSearchWholeRecordEnabled || isIterateSubelementsEnabled
                ? "text-gray-800"
                : ""
            }`}
          >
            Use attribute
          </span>
          {isAttributeEnabled && (
            <>
              <span className="text-xs ">@</span>
              <Select
                value={currentAttribute || "   "}
                onValueChange={(attributeName) => {
                  onAttributeChange(fhirField, fieldIndex, attributeName);
                }}
              >
                <SelectTrigger className="h-5 text-xs flex min-w-50">
                  <SelectValue placeholder="attr" />
                </SelectTrigger>
                <SelectContent>
                  {availableAttributes.map((attribute) => (
                    <SelectItem
                      key={attribute}
                      value={attribute.replace("@", "")}
                      className="text-xs"
                    >
                      {attribute}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </>
          )}
        </div>
      )}
    </div>
  );
}
