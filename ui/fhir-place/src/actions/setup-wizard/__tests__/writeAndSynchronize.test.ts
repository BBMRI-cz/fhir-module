import writeAndSynchronize from "../writeAndSynchronize";
import { WizardState } from "@/types/setup-wizard/types";

// Mock fetch
globalThis.fetch = jest.fn();

// Mock prepareBody
jest.mock("../mappingChangeHelper", () => ({
  prepareBody: jest.fn(() => JSON.stringify({ test: "data" })),
}));

describe("writeAndSynchronize", () => {
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

  it("should write and synchronize successfully", async () => {
    (globalThis.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue({}),
    });

    const result = await writeAndSynchronize(
      mockMappings,
      "json",
      "/test/path"
    );

    expect(result.success).toBe(true);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/change-mappings"),
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
      })
    );
  });

  it("should handle HTTP errors", async () => {
    (globalThis.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 500,
      json: jest.fn().mockResolvedValue({ error: "Server error" }),
    });

    const result = await writeAndSynchronize(
      mockMappings,
      "json",
      "/test/path"
    );

    expect(result.success).toBe(false);
  });

  it("should handle network errors", async () => {
    (globalThis.fetch as jest.Mock).mockRejectedValue(
      new Error("Network error")
    );

    const result = await writeAndSynchronize(
      mockMappings,
      "json",
      "/test/path"
    );

    expect(result.success).toBe(false);
    expect(result.errors).toBeDefined();
    expect(result.errors?.[0]).toContain("unexpected error");
  });

  it("should pass csvSeparator for CSV files", async () => {
    (globalThis.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue({}),
    });

    await writeAndSynchronize(mockMappings, "csv", "/test/path", ";");

    expect(globalThis.fetch).toHaveBeenCalled();
  });

  it("should handle non-Error exceptions", async () => {
    (globalThis.fetch as jest.Mock).mockRejectedValue("String error");

    const result = await writeAndSynchronize(
      mockMappings,
      "json",
      "/test/path"
    );

    expect(result.success).toBe(false);
    expect(result.errors?.[0]).toContain("Unknown error");
  });
});
