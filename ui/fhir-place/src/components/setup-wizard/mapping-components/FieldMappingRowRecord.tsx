import { useCallback, useContext, useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SetupWizardContext } from "@/context/SetupWizardContext";
import { DataMappingRecord } from "@/types/setup-wizard/types";
import { MappingContext } from "@/context/MappingContext";

export default function FieldMappingRowRecord({
  fhirField,
  index,
  handleDelete,
}: {
  fhirField: string;
  index: number;
  handleDelete: (index: number) => void;
}) {
  const { data, updateRecord } = useContext(MappingContext);
  const { dataFields, dataFormat } = useContext(SetupWizardContext);

  const [searchEverywhere, setSearchEverywhere] = useState<boolean>(
    data[fhirField].mappings[index].findAnywhere ?? false
  );
  const [iterateSubelements, setIterateSubelements] = useState<boolean>(
    data[fhirField].mappings[index].iterateSubelements ?? false
  );
  const [useAttribute, setUseAttribute] = useState<boolean>(
    data[fhirField].mappings[index].selectedAttribute !== undefined
  );

  const [attribute, setAttribute] = useState<string | undefined>(
    data[fhirField].mappings[index].selectedAttribute
  );

  const currentMappings = data[fhirField].mappings;

  const handleUpdate = useCallback(
    (
      index: number,
      searchEverywhere?: boolean,
      iterateSubelements?: boolean,
      attribute?: string
    ) => {
      const mapping = currentMappings[index];
      const newMapping: DataMappingRecord = {
        ...mapping,
        findAnywhere: searchEverywhere,
        iterateSubelements: iterateSubelements,
        selectedAttribute: attribute,
      };

      updateRecord(fhirField, index, newMapping);
    },
    [fhirField, currentMappings, updateRecord]
  );
  return (
    <div key={index} className="p-2 md:p-3 border rounded space-y-2">
      {/* Field Display and Remove Button */}
      <div className="flex items-start gap-2">
        <div className="flex flex-1 flex-col gap-2 min-w-0">
          <span className="text-sm md:text-base font-medium break-all">
            {currentMappings[index].value}
          </span>
          {dataFormat === "xml" && (
            <div className="flex flex-col lg:grid lg:grid-cols-12 gap-2 lg:gap-4 lg:items-center">
              <div className="flex gap-2 lg:col-span-3 items-center">
                <Checkbox
                  checked={searchEverywhere}
                  disabled={useAttribute}
                  onCheckedChange={(checked) => {
                    const value = checked as boolean;
                    setSearchEverywhere(value);
                    handleUpdate(index, value, iterateSubelements, attribute);
                  }}
                />
                <Label className="text-xs sm:text-sm">Search everywhere?</Label>
              </div>
              <div className="flex gap-2 lg:col-span-3 items-center">
                <Checkbox
                  checked={iterateSubelements}
                  disabled={useAttribute}
                  onCheckedChange={(checked) => {
                    const value = checked as boolean;
                    setIterateSubelements(value);
                    handleUpdate(index, searchEverywhere, value, attribute);
                  }}
                />
                <Label className="text-xs sm:text-sm">
                  Iterate sub-elements?
                </Label>
              </div>
              <div className="flex flex-col sm:grid sm:grid-cols-6 lg:col-span-6 gap-2">
                {!!(
                  dataFields.find(
                    (field) => field.path === currentMappings[index].value
                  ) ?? {}
                )?.attributes?.length && (
                  <div className="flex sm:col-span-2 gap-2 items-center">
                    <Checkbox
                      checked={useAttribute}
                      disabled={searchEverywhere || iterateSubelements}
                      onCheckedChange={(checked) => {
                        const value = checked as boolean;
                        if (!value) {
                          setAttribute(undefined);
                          handleUpdate(
                            index,
                            searchEverywhere,
                            iterateSubelements,
                            undefined
                          );
                        }

                        setUseAttribute(value);
                      }}
                    />
                    <Label className="text-xs sm:text-sm">Use attribute?</Label>
                  </div>
                )}
                {useAttribute && (
                  <div className="sm:col-span-4">
                    <Select
                      value={attribute}
                      onValueChange={(value) => {
                        setAttribute(value);
                        handleUpdate(
                          index,
                          searchEverywhere,
                          iterateSubelements,
                          value
                        );
                      }}
                    >
                      <SelectTrigger className="w-full h-9 text-sm">
                        <SelectValue placeholder="Select the attribute" />
                      </SelectTrigger>
                      <SelectContent>
                        {(
                          dataFields.find(
                            (field) =>
                              field.path === currentMappings[index].value
                          ) ?? {}
                        )?.attributes?.map((field) => (
                          <SelectItem
                            key={field}
                            value={field}
                            className="py-2 text-sm"
                          >
                            <span className="flex items-center w-full">
                              {field}
                            </span>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => {
            handleDelete(index);
          }}
          className="h-6 w-6 p-0 text-red-500 hover:text-red-700 shrink-0"
          title="Remove field"
        >
          ×
        </Button>
      </div>
    </div>
  );
}
