"use client";
import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { DataMappingRecord, DataRecord } from "@/types/setup-wizard/types";
import { MappingContextType } from "@/types/context/mapping-context/types";

export const MappingContext = createContext<MappingContextType>({
  data: {},
  setData: () => {},
  addRecord: () => {},
  updateRecord: () => {},
  deleteRecord: () => {},
});

export function MappingContextProvider({
  children,
  initialData,
}: {
  children: React.ReactNode;
  initialData: Record<string, DataRecord>;
}) {
  const [data, setData] = useState<Record<string, DataRecord>>(initialData);

  useEffect(() => {
    setData(initialData);
  }, [initialData]);

  const addRecord = useCallback((key: string, newValue: string) => {
    setData((prev) => {
      const newData = {
        ...prev,
        [key]: {
          ...prev[key],
          mappings: [
            ...prev[key].mappings,
            {
              value: newValue,
            },
          ],
        },
      };
      return newData;
    });
  }, []);

  const updateRecord = useCallback(
    (key: string, index: number, newValue: DataMappingRecord) => {
      setData((prev) => {
        const mappings = [...prev[key].mappings];
        mappings[index] = newValue;

        const newData = {
          ...prev,
          [key]: {
            ...prev[key],
            mappings,
          },
        };
        return newData;
      });
    },
    []
  );

  const deleteRecord = useCallback((key: string, index: number) => {
    setData((prev) => {
      const newArray = prev[key].mappings.filter(
        (record, idx) => idx !== index
      );

      const newData = {
        ...prev,
        [key]: {
          ...prev[key],
          mappings: newArray,
        },
      };
      return newData;
    });
  }, []);

  const contextValue = useMemo(
    () => ({ data, setData, addRecord, updateRecord, deleteRecord }),
    [data, addRecord, updateRecord, deleteRecord]
  );

  return (
    <MappingContext.Provider value={contextValue}>
      {children}
    </MappingContext.Provider>
  );
}
