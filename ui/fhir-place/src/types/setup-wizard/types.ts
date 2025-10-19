import { EntityMap } from "@/types/actions/configuration-details/types";

export type SyncTarget = "blaze" | "miabis" | "both";

export type SyncTargetConfig = "blazeConfig" | "miabisConfig";

export type EnumDefinitionStep = "material" | "temperature";

export type DefinitionStep =
  | "donor"
  | "sample"
  | "condition"
  | "typeToCollection";

export type DataRecord = {
  isRequired: boolean;
  mappings: DataMappingRecord[];
  resultPath?: string;
  xmlDependsOn?: string;
  onlyForFormats?: string[];
};

export type DataMappingRecord = {
  value: string;
  selectedAttribute?: string;
  findAnywhere?: boolean;
  iterateSubelements?: boolean;
};

export interface EnumMapping {
  userValue: string;
  apiValue: string;
}

export interface MappingConfig {
  title: string;
  dataFetcher: (isMiabis: boolean) => Promise<string[]>;
  wizardStateMapping: (
    prev: WizardState,
    targetConfig: SyncTargetConfig,
    update: EnumMapping[]
  ) => WizardState;
  wizardStateFetchFunction: (
    state: WizardState,
    targetConfig: SyncTargetConfig
  ) => EnumMapping[];
  allowCustomValuesGetter: (
    state: WizardState,
    targetConfig: SyncTargetConfig
  ) => boolean;
  allowCustomValuesSetter: (
    prev: WizardState,
    targetConfig: SyncTargetConfig,
    value: boolean
  ) => WizardState;
}

export interface CommonMappingConfig {
  title: string;
  dataFetcher: () => Promise<string[]>;
  wizardStateMapping: (prev: WizardState, update: EnumMapping[]) => WizardState;
  wizardStateFetchFunction: (state: WizardState) => EnumMapping[];
}

export interface CommonEnumMappingProps {
  config: CommonMappingConfig;
  nextStep: () => void;
  previousStep?: () => void;
}

export interface DefineEnumMappingProps {
  config: MappingConfig;
  nextStep: () => void;
  previousStep?: () => void;
  targetConfig: SyncTargetConfig;
}

export interface CustomMappingConfig {
  title: string;
  getMappingSchema: () => Promise<EntityMap>;
  wizardStateMapping: (
    prev: WizardState,
    update: Record<string, DataRecord>
  ) => WizardState;
  wizardStateFetchFunction: (state: WizardState) => Record<string, DataRecord>;
}
export interface CustomMappingStepProps {
  config: CustomMappingConfig;
  nextStep: () => void;
  previousStep?: () => void;
}

export type SingleSyncConfig = {
  temperatureMapping: EnumMapping[];
  materialMapping: EnumMapping[];
  allowCustomMaterialValues: boolean;
  allowCustomTemperatureValues: boolean;
};

export type SharedMappings = {
  donorMapping: Record<string, DataRecord>;
  sampleMapping: Record<string, DataRecord>;
  conditionMapping: Record<string, DataRecord>;
  typeToCollectionMapping: EnumMapping[];
};

export type WizardState = {
  syncTarget: SyncTarget;
  sharedMappings: SharedMappings;
  blazeConfig: SingleSyncConfig;
  miabisConfig: SingleSyncConfig;
};

export type ManualEditorComponentProps = {
  currentMappings: EnumMapping[];
  availableOptions: string[];
  onChange: (json: string, hasError: boolean) => void;
  allowCustomValues?: boolean;
};

export type VisualEditorComponentProps = {
  title: string;
  mappings: EnumMapping[];
  addMapping: () => void;
  updateMapping: (
    index: number,
    field: keyof EnumMapping,
    value: string
  ) => void;
  removeMapping: (index: number) => void;
  availableOptions: string[];
  allowCustomValues?: boolean;
};

export type ValidationResult = {
  success: boolean;
  genericErrors?: string[];
  patientErrors?: string[];
  sampleErrors?: string[];
  conditionErrors?: string[];
};

export type ConfigChangeBodyRequest = {
  fileType: string;
  recordsPath: string;
  mappings: WizardState;
  csvSeparator?: string;
  validateAllFiles?: boolean;
  syncTarget?: SyncTarget;
};
