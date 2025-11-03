export type SimpleKeyInfo = {
  required: boolean;
  onlyForFormats?: string[];
  xmlDependsOn?: string;
  saveToPath?: string;
};

export interface EntityMap {
  [key: string]: SimpleKeyInfo;
}

export interface DonorMap extends EntityMap {
  gender: SimpleKeyInfo;
  birthDate: SimpleKeyInfo;
}

export interface SampleMap extends EntityMap {
  id: SimpleKeyInfo;
  material_type: SimpleKeyInfo;
  diagnosis: SimpleKeyInfo;
  diagnosis_date: SimpleKeyInfo;
  collection_date: SimpleKeyInfo;
  storage_temperature: SimpleKeyInfo;
  collection: SimpleKeyInfo;
  donor_id: SimpleKeyInfo;
  sample: SimpleKeyInfo;
}

export interface ConditionMap extends EntityMap {
  "icd-10_code": SimpleKeyInfo;
  patient_id: SimpleKeyInfo;
  diagnosis_date: SimpleKeyInfo;
}

export type EnumInfo = {
  storage_temperature: string[];
  material_type: string[];
};

export type DataField = {
  name: string;
  path: string;
  example?: string;
  attributes?: string[];
};

export type ParsedDataResult = {
  success: boolean;
  message: string;
  fields?: DataField[];
};
