import {
  mapEnumMappingToJson,
  mappingRecordToJson,
} from "@/lib/json/json-utils";
import { ConfigChangeBodyRequest } from "@/types/setup-wizard/types";

export function prepareBody(
  request: ConfigChangeBodyRequest
): string | undefined {
  const {
    fileType,
    recordsPath,
    mappings,
    csvSeparator,
    validateAllFiles,
    syncTarget,
  } = request;
  const { sharedMappings, blazeConfig, miabisConfig } = mappings;

  const blazeTemperatureMappingJson = mapEnumMappingToJson(
    blazeConfig.temperatureMapping
  );
  const blazeMaterialMappingJson = mapEnumMappingToJson(
    blazeConfig.materialMapping
  );
  const miabisTemperatureMappingJson = mapEnumMappingToJson(
    miabisConfig.temperatureMapping
  );
  const miabisMaterialMappingJson = mapEnumMappingToJson(
    miabisConfig.materialMapping
  );
  const typeToCollectionMappingJson = mapEnumMappingToJson(
    sharedMappings.typeToCollectionMapping
  );
  const donorMappingJson = mappingRecordToJson(
    sharedMappings.donorMapping,
    true
  );
  const sampleMappingJson = mappingRecordToJson(
    sharedMappings.sampleMapping,
    true
  );
  const conditionMappingJson = mappingRecordToJson(
    sharedMappings.conditionMapping,
    true
  );

  return JSON.stringify({
    blaze_temperature_mapping:
      Object.keys(blazeTemperatureMappingJson).length > 0
        ? blazeTemperatureMappingJson
        : undefined,
    blaze_material_mapping:
      Object.keys(blazeMaterialMappingJson).length > 0
        ? blazeMaterialMappingJson
        : undefined,
    miabis_temperature_mapping:
      Object.keys(miabisTemperatureMappingJson).length > 0
        ? miabisTemperatureMappingJson
        : undefined,
    miabis_material_mapping:
      Object.keys(miabisMaterialMappingJson).length > 0
        ? miabisMaterialMappingJson
        : undefined,
    type_to_collection_mapping:
      Object.keys(typeToCollectionMappingJson).length > 0
        ? typeToCollectionMappingJson
        : undefined,
    donor_mapping:
      Object.keys(donorMappingJson).length > 0 ? donorMappingJson : undefined,
    sample_mapping:
      Object.keys(sampleMappingJson).length > 0 ? sampleMappingJson : undefined,
    condition_mapping:
      Object.keys(conditionMappingJson).length > 0
        ? conditionMappingJson
        : undefined,
    file_type: fileType,
    test_records_path: recordsPath.replaceAll("\\", "/"),
    csv_separator: fileType === "csv" ? csvSeparator : undefined,
    validate_all_files: validateAllFiles,
    sync_target: syncTarget,
  });
}
