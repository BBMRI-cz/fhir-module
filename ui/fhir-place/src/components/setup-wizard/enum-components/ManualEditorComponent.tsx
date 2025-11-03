import { Textarea } from "@/components/ui/textarea";
import { useRef, useState } from "react";
import { ManualEditorComponentProps } from "@/types/setup-wizard/types";
import { mapEnumMappingToJson, validateEnumJson } from "@/lib/json/json-utils";

export default function ManualEditorComponent(
  props: ManualEditorComponentProps
) {
  const {
    currentMappings,
    availableOptions,
    onChange,
    allowCustomValues = false,
  } = props;
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [manualJson, setManualJson] = useState(
    mapEnumMappingToJson(currentMappings)
  );

  const debounceTimer = useRef<NodeJS.Timeout | null>(null);
  const handleManualJsonChange = (value: string) => {
    setManualJson(value);

    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(() => {
      try {
        const obj = JSON.parse(value);

        const optionsToValidate = allowCustomValues ? [] : availableOptions;
        const validation = validateEnumJson(obj, optionsToValidate);
        if (!validation.valid) {
          setJsonError(validation.error!);
          onChange(value, true);
          return;
        }

        setJsonError(null);

        onChange(value, false);
      } catch (error) {
        setJsonError((error as SyntaxError).message);
        onChange(value, true);
      }
    }, 500);
  };

  return (
    <div className="flex-1 flex gap-4 overflow-hidden">
      {/* Left Column - JSON Editor */}
      <div className="flex-1 rounded-lg border shadow-sm flex flex-col min-w-0">
        <div className="p-3 md:p-4 border-b">
          <h4 className="text-base md:text-lg font-medium">
            Manual JSON Mapping
          </h4>
        </div>
        <div className="flex-1 p-3 md:p-4 flex flex-col min-h-0">
          <Textarea
            value={manualJson}
            onChange={(e) => handleManualJsonChange(e.target.value)}
            className="font-mono text-sm flex-1 resize-none min-h-0"
          />
          {jsonError && (
            <div className="text-sm text-red-600 bg-red-50 p-3 rounded mt-2 flex-shrink-0">
              <strong>JSON Error:</strong> {jsonError}
            </div>
          )}
        </div>
      </div>

      {availableOptions.length > 0 && (
        <div className="hidden xl:flex xl:w-80 2xl:w-96 rounded-lg border shadow-sm flex-col">
          <div className="p-4 border-b">
            <h4 className="text-lg font-medium">Available values</h4>
          </div>
          <div className="flex-1 p-4 overflow-y-auto">
            <div className="space-y-2">
              {availableOptions.map((option) => (
                <div
                  key={option}
                  className="p-2 border rounded text-sm bg-muted/50"
                >
                  <div className="font-mono font-medium">{option}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
