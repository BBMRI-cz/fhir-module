import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, Trash2 } from "lucide-react";
import { VisualEditorComponentProps } from "@/types/setup-wizard/types";
import CustomValueSelect from "@/components/setup-wizard/enum-components/CustomValueSelect";

export default function VisualEditorComponent(
  props: VisualEditorComponentProps
) {
  const {
    title,
    mappings,
    addMapping,
    updateMapping,
    removeMapping,
    availableOptions,
    allowCustomValues = false,
  } = props;
  return (
    <div className="flex-1 flex gap-4 overflow-hidden">
      {/* Left Column - Mapping Configuration */}
      <div className="flex-1 rounded-lg border shadow-sm flex flex-col min-w-0">
        <div className="flex items-center justify-between p-3 md:p-4 border-b gap-2">
          <h4 className="text-base md:text-lg font-medium truncate">
            {title} Mappings
          </h4>
          <Button
            onClick={addMapping}
            size="sm"
            className="flex items-center gap-1 h-8 text-sm px-2 shrink-0"
          >
            <Plus className="w-4 h-4" />
            <span className="hidden sm:inline">Add Mapping</span>
            <span className="sm:hidden">Add</span>
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 md:p-4 space-y-3">
          {mappings.map((mapping, index) => {
            return (
              <div
                key={index} // NOSONAR
                className="flex flex-col sm:flex-row sm:items-end gap-2 p-3 border rounded-lg"
              >
                <div className="flex-1 min-w-0">
                  <Label
                    htmlFor={`user-value-${index}`}
                    className="text-sm font-medium"
                  >
                    Your Data Value
                  </Label>
                  <Input
                    id={`user-value-${index}`}
                    placeholder="Value in your data"
                    value={mapping.userValue}
                    onChange={(e) =>
                      updateMapping(index, "userValue", e.target.value)
                    }
                    className="mt-1 h-9 text-sm"
                  />
                </div>

                <div className="flex-1 min-w-0">
                  <Label
                    htmlFor={`api-value-${index}`}
                    className="text-sm font-medium"
                  >
                    FHIR Value
                  </Label>
                  <div className="mt-1">
                    <CustomValueSelect
                      value={mapping.apiValue}
                      onValueChange={(value) =>
                        updateMapping(index, "apiValue", value)
                      }
                      availableOptions={availableOptions}
                      allowCustomValues={allowCustomValues}
                      placeholder="Select value"
                    />
                  </div>
                </div>

                <Button
                  onClick={() => removeMapping(index)}
                  variant="outline"
                  size="sm"
                  className="h-9 px-3 sm:w-auto w-full sm:mt-0 mt-1"
                >
                  <Trash2 className="w-4 h-4 sm:mr-0 mr-2" />
                  <span className="sm:hidden">Remove</span>
                </Button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Right Column - Preview (hidden on smaller screens) */}
      <div className="hidden xl:flex xl:w-80 2xl:w-96 rounded-lg border shadow-sm flex-col">
        <div className="p-4 border-b">
          <h4 className="text-lg font-medium">Mapping Preview</h4>
        </div>
        <div className="flex-1 p-4 overflow-hidden">
          <div className="p-3 rounded-lg font-mono text-xs h-full overflow-auto">
            <pre>
              {JSON.stringify(
                mappings
                  .filter((m) => m.userValue.trim() && m.apiValue.trim())
                  .reduce(
                    (acc, m) => ({ ...acc, [m.userValue]: m.apiValue }),
                    {}
                  ),
                null,
                2
              )}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
