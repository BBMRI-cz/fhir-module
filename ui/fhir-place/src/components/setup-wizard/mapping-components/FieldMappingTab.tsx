import { useContext, useEffect, useState } from "react";
import { FieldMappingRow } from "@/components/setup-wizard/mapping-components/FieldMappingRow";
import { MappingContext } from "@/context/MappingContext";
import { SetupWizardContext } from "@/context/SetupWizardContext";
import { mappingRecordToJson } from "@/lib/json/json-utils";
import { DataRecord } from "@/types/setup-wizard/types";
interface FieldMappingTabProps {
  mappingConceptName: string;
}

export function FieldMappingTab({ mappingConceptName }: FieldMappingTabProps) {
  const { data } = useContext(MappingContext);

  const { dataFormat } = useContext(SetupWizardContext);

  const [jsonData, setJsonData] = useState<string>("{}");

  useEffect(() => {
    setJsonData(mappingRecordToJson(data));
  }, [data]);

  function mapReadyValues(data: Record<string, DataRecord>) {
    if (!dataFormat) return;

    let keys = Object.keys(data);
    keys = keys.filter((key) => {
      if (data[key].onlyForFormats !== undefined) {
        return data[key].onlyForFormats?.includes(dataFormat);
      }

      return data[key].onlyForFormats === undefined;
    });

    keys = keys.filter((key) => {
      const x = data[key];
      if (!x.xmlDependsOn) {
        return true;
      }

      if (!keys.includes(x.xmlDependsOn)) {
        return true;
      }

      const parentMappings = data[x.xmlDependsOn].mappings;
      return !!parentMappings.length;
    });

    keys = keys.sort((a, b) =>
      prepareSortString(data[a], a).localeCompare(prepareSortString(data[b], b))
    );

    return keys.map((key) => (
      <div
        key={key}
        className={
          dataFormat === "xml" &&
          data[key]?.xmlDependsOn &&
          keys.includes(data[key]?.xmlDependsOn)
            ? "pl-6"
            : ""
        }
      >
        <FieldMappingRow fhirField={key} />
      </div>
    ));

    function prepareSortString(dataRecord: DataRecord, key: string) {
      let result = "";

      if (dataRecord?.xmlDependsOn) {
        result += dataRecord.xmlDependsOn;
      }

      if (dataRecord.isRequired) {
        result += " ";
      }
      return result + key;
    }
  }

  return (
    <div className="flex-1 flex gap-4 overflow-hidden">
      {/* Left Column - Field Mapping */}
      <div className="flex-1 rounded-lg border shadow-sm flex flex-col min-w-0">
        <div className="p-3 md:p-4 border-b">
          <h4 className="text-base md:text-lg font-medium">Field Mapping</h4>
          <span className="text-xs md:text-sm text-gray-600 mt-1">
            Map your data fields to FHIR {mappingConceptName} fields
          </span>
        </div>
        <div className="flex-1 p-3 md:p-4 overflow-y-auto">
          <div className="space-y-3">{data && mapReadyValues(data)}</div>
        </div>
      </div>

      {/* Right Column - Preview (hidden on smaller screens) */}
      <div className="hidden xl:flex xl:w-80 2xl:w-96 rounded-lg border shadow-sm flex-col">
        <div className="p-4 border-b">
          <h4 className="text-lg font-medium">Mapping Preview</h4>
        </div>
        <div className="flex-1 p-4 overflow-hidden">
          <div className="p-3 rounded-lg font-mono text-xs h-full overflow-auto">
            <pre>{jsonData}</pre>
          </div>
        </div>
      </div>
    </div>
  );
}
