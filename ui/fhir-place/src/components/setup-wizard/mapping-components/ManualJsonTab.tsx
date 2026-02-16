import { Textarea } from "@/components/ui/textarea";
import { useRef, useState } from "react";
import {
  mappingRecordToJson,
  parseJsonToMappingRecord,
} from "@/lib/json/json-utils";
import { DataMappingRecord, DataRecord } from "@/types/setup-wizard/types";
import { DataField } from "@/types/actions/configuration-details/types";

interface ManualJsonTabProps {
  currentMappings: Record<string, DataRecord>;
  availableOptions: DataField[];
  onChange: (
    value: Record<string, DataMappingRecord[]>,
    hasError: boolean
  ) => void;
}

export function ManualJsonTab(props: ManualJsonTabProps) {
  const { availableOptions, onChange } = props;
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [manualJson, setManualJson] = useState<string>(
    mappingRecordToJson(props.currentMappings)
  );

  const debounceTimer = useRef<NodeJS.Timeout | null>(null);
  const onManualJsonChange = (value: string) => {
    setManualJson(value);

    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(() => {
      try {
        const obj = JSON.parse(value);

        setJsonError(null);

        const { valid, error, record } = parseJsonToMappingRecord(
          obj,
          availableOptions
        );
        if (!valid) {
          setJsonError(error!);
          onChange({}, true);
          return;
        }
        onChange(record!, false);
      } catch (error) {
        setJsonError((error as SyntaxError).message);
        onChange({}, true);
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
            onChange={(e) => onManualJsonChange(e.target.value)}
            className="font-mono text-sm flex-1 resize-none min-h-0"
            placeholder={"{}"}
          />
          {jsonError && (
            <div className="text-sm text-red-600 bg-red-50 p-3 rounded mt-2 flex-shrink-0">
              <strong>JSON Error:</strong> {jsonError}
            </div>
          )}
        </div>
      </div>

      {/* Right Column - Available FHIR Fields (hidden on smaller screens) */}
      <div className="hidden xl:flex xl:w-80 2xl:w-96 rounded-lg border shadow-sm flex-col">
        <div className="p-4 border-b">
          <h4 className="text-lg font-medium">Available FHIR Fields</h4>
        </div>
        <div className="flex-1 p-4 overflow-y-auto">
          <div className="space-y-2">
            {Object.entries({}).map(([field]) => (
              <div key={field} className="p-2 border rounded text-sm">
                <div className="font-mono font-medium">{field}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
