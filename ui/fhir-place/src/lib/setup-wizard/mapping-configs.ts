import {
  getConditionMappingSchema,
  getDonorMappingSchema,
  getTemperatureValues,
  getSampleMappingSchema,
} from "@/actions/configuration-details/configuration-details-actions";
import { getMaterialTypes } from "@/actions/configuration/material-types";
import {
  CommonMappingConfig,
  CustomMappingConfig,
  DataRecord,
  EnumMapping,
  MappingConfig,
  SyncTargetConfig,
  WizardState,
} from "@/types/setup-wizard/types";

export const materialConfig: MappingConfig = {
  title: "Material Type Mapping",
  dataFetcher: async (isMiabis: boolean) => {
    const data = await getMaterialTypes(isMiabis);
    return data;
  },
  wizardStateMapping: (
    prev: WizardState,
    targetConfig: SyncTargetConfig,
    update: EnumMapping[]
  ) => {
    return {
      ...prev,
      [targetConfig]: {
        ...prev[targetConfig],
        materialMapping: update,
      },
    };
  },
  wizardStateFetchFunction: (
    state: WizardState,
    targetConfig: SyncTargetConfig
  ) => state[targetConfig].materialMapping,
  allowCustomValuesGetter: (
    state: WizardState,
    targetConfig: SyncTargetConfig
  ) => state[targetConfig].allowCustomMaterialValues,
  allowCustomValuesSetter: (
    prev: WizardState,
    targetConfig: SyncTargetConfig,
    value: boolean
  ) => ({
    ...prev,
    [targetConfig]: {
      ...prev[targetConfig],
      allowCustomMaterialValues: value,
    },
  }),
};

export const temperatureConfig: MappingConfig = {
  title: "Storage Temperature Mapping",
  dataFetcher: async () => {
    const data = await getTemperatureValues();
    return data;
  },
  wizardStateMapping: (
    prev: WizardState,
    targetConfig: SyncTargetConfig,
    update: EnumMapping[]
  ) => {
    return {
      ...prev,
      [targetConfig]: {
        ...prev[targetConfig],
        temperatureMapping: update,
      },
    };
  },
  wizardStateFetchFunction: (
    state: WizardState,
    targetConfig: SyncTargetConfig
  ) => state[targetConfig].temperatureMapping,
  allowCustomValuesGetter: (
    state: WizardState,
    targetConfig: SyncTargetConfig
  ) => state[targetConfig].allowCustomTemperatureValues,
  allowCustomValuesSetter: (
    prev: WizardState,
    targetConfig: SyncTargetConfig,
    value: boolean
  ) => ({
    ...prev,
    [targetConfig]: {
      ...prev[targetConfig],
      allowCustomTemperatureValues: value,
    },
  }),
};

export const typeToCollectionConfig: CommonMappingConfig = {
  title: "Type to Collection Mapping",
  dataFetcher: async () => {
    return [];
  },
  wizardStateMapping: (prev: WizardState, update: EnumMapping[]) => {
    return {
      ...prev,
      sharedMappings: {
        ...prev.sharedMappings,
        typeToCollectionMapping: update,
      },
    };
  },
  wizardStateFetchFunction: (state: WizardState) =>
    state.sharedMappings.typeToCollectionMapping,
};

export const donorMappingConfig: CustomMappingConfig = {
  title: "Donor",
  getMappingSchema: getDonorMappingSchema,
  wizardStateMapping: (
    prev: WizardState,
    update: Record<string, DataRecord>
  ) => {
    return {
      ...prev,
      sharedMappings: {
        ...prev.sharedMappings,
        donorMapping: update,
      },
    };
  },
  wizardStateFetchFunction: (state: WizardState) =>
    state.sharedMappings.donorMapping,
};

export const conditionMappingConfig: CustomMappingConfig = {
  title: "Condition",
  getMappingSchema: getConditionMappingSchema,
  wizardStateMapping: (
    prev: WizardState,
    update: Record<string, DataRecord>
  ) => {
    return {
      ...prev,
      sharedMappings: {
        ...prev.sharedMappings,
        conditionMapping: update,
      },
    };
  },
  wizardStateFetchFunction: (state: WizardState) =>
    state.sharedMappings.conditionMapping,
};

export const sampleMappingConfig: CustomMappingConfig = {
  title: "Sample",
  getMappingSchema: getSampleMappingSchema,
  wizardStateMapping: (
    prev: WizardState,
    update: Record<string, DataRecord>
  ) => {
    return {
      ...prev,
      sharedMappings: {
        ...prev.sharedMappings,
        sampleMapping: update,
      },
    };
  },
  wizardStateFetchFunction: (state: WizardState) =>
    state.sharedMappings.sampleMapping,
};
