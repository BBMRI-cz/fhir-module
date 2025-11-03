import { validateMappings } from "../validateMappings";
import { WizardState } from "@/types/setup-wizard/types";

// Mock fetch
globalThis.fetch = jest.fn();

// Mock prepareBody
jest.mock("../mappingChangeHelper", () => ({
  prepareBody: jest.fn(() => JSON.stringify({ test: "data" })),
}));

describe("validateMappings", () => {
  const mockMappings: WizardState = {
    temperatureMapping: [],
    materialMapping: [],
    donorMapping: {},
    sampleMapping: {},
    conditionMapping: {},
    typeToCollectionMapping: [],
    allowCustomMaterialValues: false,
    allowCustomTemperatureValues: false,
    allowCustomTypeToCollectionValues: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should validate mappings successfully", async () => {
    (globalThis.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue({}),
    });

    const result = await validateMappings(mockMappings, "json", "/test/path");

    expect(result.success).toBe(true);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/validate-mappings"),
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
      })
    );
  });

  it("should handle validation errors from backend", async () => {
    const errorResponse = {
      message: {
        generic_errors: ["Invalid mapping"],
        patient_errors: ["Patient field missing"],
        sample_errors: [],
        condition_errors: [],
      },
    };

    (globalThis.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      json: jest.fn().mockResolvedValue(errorResponse),
    });

    const result = await validateMappings(mockMappings, "json", "/test/path");

    expect(result.success).toBe(false);
    expect(result.genericErrors).toEqual(["Invalid mapping"]);
    expect(result.patientErrors).toEqual(["Patient field missing"]);
  });

  it("should handle string error messages", async () => {
    const errorResponse = {
      message: "Server error occurred",
    };

    (globalThis.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      json: jest.fn().mockResolvedValue(errorResponse),
    });

    const result = await validateMappings(mockMappings, "json", "/test/path");

    expect(result.success).toBe(false);
  });

  it("should pass csvSeparator for CSV files", async () => {
    (globalThis.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue({}),
    });

    await validateMappings(mockMappings, "csv", "/test/path", ";");

    expect(globalThis.fetch).toHaveBeenCalled();
  });

  it("should handle validateAllFiles option", async () => {
    (globalThis.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue({}),
    });

    await validateMappings(mockMappings, "json", "/test/path", undefined, true);

    expect(globalThis.fetch).toHaveBeenCalled();
  });

  it("should handle network errors", async () => {
    (globalThis.fetch as jest.Mock).mockRejectedValue(
      new Error("Network error")
    );

    const result = await validateMappings(mockMappings, "json", "/test/path");

    expect(result.success).toBe(false);
    expect(result.genericErrors).toBeDefined();
    expect(result.genericErrors?.[0]).toContain("unexpected error");
  });

  it("should handle non-Error exceptions", async () => {
    (globalThis.fetch as jest.Mock).mockRejectedValue("String error");

    const result = await validateMappings(mockMappings, "json", "/test/path");

    expect(result.success).toBe(false);
    expect(result.genericErrors?.[0]).toContain("Unknown error");
  });
});
