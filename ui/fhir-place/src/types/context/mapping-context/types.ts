import { DataMappingRecord, DataRecord } from "@/types/setup-wizard/types";

export type MappingContextType = {
  data: Record<string, DataRecord>;
  setData: (data: Record<string, DataRecord>) => void;
  addRecord(key: string, newValue: string): void;
  updateRecord(key: string, index: number, newValue: DataMappingRecord): void;
  deleteRecord(key: string, index: number): void;
};
