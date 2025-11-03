import { prepareBody } from "../mappingChangeHelper";
import {
  ConfigChangeBodyRequest,
  WizardState,
} from "@/types/setup-wizard/types";

/* eslint-disable @typescript-eslint/no-explicit-any */
jest.mock("@/lib/json/json-utils", () => ({
  mapEnumMappingToJson: jest.fn((mapping) => {
    return mapping.reduce((acc: Record<string, string>, item: any) => {
      if (item.userValue && item.apiValue) {
        acc[item.userValue] = item.apiValue;
      }
      return acc;
    }, {});
  }),
  mappingRecordToJson: jest.fn((mapping) => {
    return { ...mapping };
  }),
}));

describe("prepareBody", () => {
  const mockMappings: WizardState = {
    syncTarget: "blaze",
    sharedMappings: {
      donorMapping: {
        id: { mappings: [], isRequired: true },
        gender: { mappings: [], isRequired: false },
      },
      sampleMapping: {
        id: { mappings: [], isRequired: true },
      },
      conditionMapping: {
        "icd-10_code": { mappings: [], isRequired: true },
      },
      typeToCollectionMapping: [
        { userValue: "blood", apiValue: "BLOOD" },
      ],
    },
    blazeConfig: {
      temperatureMapping: [
        { userValue: "cold", apiValue: "MINUS_20" },
        { userValue: "frozen", apiValue: "MINUS_80" },
      ],
      materialMapping: [{ userValue: "blood", apiValue: "BLOOD" }],
      allowCustomMaterialValues: false,
      allowCustomTemperatureValues: false,
    },
    miabisConfig: {
      temperatureMapping: [
        { userValue: "cold", apiValue: "MINUS_20" },
        { userValue: "frozen", apiValue: "MINUS_80" },
      ],
      materialMapping: [{ userValue: "blood", apiValue: "BLOOD" }],
      allowCustomMaterialValues: false,
      allowCustomTemperatureValues: false,
    },
  };

  it("should prepare body with all mappings", () => {
    const request: ConfigChangeBodyRequest = {
      fileType: "json",
      recordsPath: "/test/path",
      mappings: mockMappings,
    };

    const result = prepareBody(request);

    expect(result).toBeDefined();
    const parsed = JSON.parse(result!);

    expect(parsed.file_type).toBe("json");
    expect(parsed.test_records_path).toBe("/test/path");
    expect(parsed.blaze_temperature_mapping).toBeDefined();
    expect(parsed.blaze_material_mapping).toBeDefined();
    expect(parsed.miabis_temperature_mapping).toBeDefined();
    expect(parsed.miabis_material_mapping).toBeDefined();
    expect(parsed.donor_mapping).toBeDefined();
    expect(parsed.sample_mapping).toBeDefined();
    expect(parsed.condition_mapping).toBeDefined();
    expect(parsed.type_to_collection_mapping).toBeDefined();
  });

  it("should handle CSV file type with separator", () => {
    const request: ConfigChangeBodyRequest = {
      fileType: "csv",
      recordsPath: "/test/path",
      mappings: mockMappings,
      csvSeparator: ";",
    };

    const result = prepareBody(request);
    const parsed = JSON.parse(result!);

    expect(parsed.file_type).toBe("csv");
    expect(parsed.csv_separator).toBe(";");
  });

  it("should not include csv_separator for non-CSV files", () => {
    const request: ConfigChangeBodyRequest = {
      fileType: "json",
      recordsPath: "/test/path",
      mappings: mockMappings,
      csvSeparator: ";",
    };

    const result = prepareBody(request);
    const parsed = JSON.parse(result!);

    expect(parsed.csv_separator).toBeUndefined();
  });

  it("should convert backslashes to forward slashes in path", () => {
    const request: ConfigChangeBodyRequest = {
      fileType: "json",
      recordsPath: String.raw`C:\Users\test\path`,
      mappings: mockMappings,
    };

    const result = prepareBody(request);
    const parsed = JSON.parse(result!);

    expect(parsed.test_records_path).toBe("C:/Users/test/path");
  });

  it("should handle validateAllFiles option", () => {
    const request: ConfigChangeBodyRequest = {
      fileType: "json",
      recordsPath: "/test/path",
      mappings: mockMappings,
      validateAllFiles: true,
    };

    const result = prepareBody(request);
    const parsed = JSON.parse(result!);

    expect(parsed.validate_all_files).toBe(true);
  });

  it("should handle empty mappings", () => {
    const emptyMappings: WizardState = {
      syncTarget: "both",
      sharedMappings: {
        donorMapping: {},
        sampleMapping: {},
        conditionMapping: {},
        typeToCollectionMapping: [],
      },
      blazeConfig: {
        temperatureMapping: [],
        materialMapping: [],
        allowCustomMaterialValues: false,
        allowCustomTemperatureValues: false,
      },
      miabisConfig: {
        temperatureMapping: [],
        materialMapping: [],
        allowCustomMaterialValues: false,
        allowCustomTemperatureValues: false,
      },
    };

    const request: ConfigChangeBodyRequest = {
      fileType: "json",
      recordsPath: "/test/path",
      mappings: emptyMappings,
    };

    const result = prepareBody(request);
    const parsed = JSON.parse(result!);

    // Empty mappings should be undefined in the output
    expect(parsed.temperature_mapping).toBeUndefined();
    expect(parsed.material_mapping).toBeUndefined();
    expect(parsed.donor_mapping).toBeUndefined();
    expect(parsed.sample_mapping).toBeUndefined();
    expect(parsed.condition_mapping).toBeUndefined();
  });
});
