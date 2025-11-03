import { SharedMappings, SingleSyncConfig } from "@/types/setup-wizard/types";

export function getEmptySyncConfig(): SingleSyncConfig {
  return {
    temperatureMapping: [],
    materialMapping: [],
    allowCustomMaterialValues: false,
    allowCustomTemperatureValues: false,
  };
}

export function getEmptySharedMappings(): SharedMappings {
  return {
    donorMapping: {},
    sampleMapping: {},
    conditionMapping: {},
    typeToCollectionMapping: [],
  };
}
