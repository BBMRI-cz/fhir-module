import {
  getDonorMappingSchema,
  getSampleMappingSchema,
  getConditionMappingSchema,
  getTemperatureValues,
  parseDataFromFolder,
  clearCache,
} from "@/actions/configuration-details/configuration-details-actions";
import { parseMultipleFolderData } from "@/actions/folder/parse-folder-data";

// Mock fetch globally
globalThis.fetch = jest.fn();

// Mock parseMultipleFolderData (which is what parseDataFromFolder uses internally)
jest.mock("@/actions/folder/parse-folder-data", () => ({
  parseMultipleFolderData: jest.fn(),
}));
const mockParseMultipleFolderData = parseMultipleFolderData as jest.MockedFunction<
  typeof parseMultipleFolderData
>;

describe("configuration-details-actions", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    clearCache();
  });

  describe("getDonorMappingSchema", () => {
    it("should fetch and normalize donor mapping schema", async () => {
      const mockResponse = {
        id: { required: true },
        gender: { required: false },
        birth_date: { required: true, only_for_formats: ["CSV", "JSON"] },
      };

      (globalThis.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      const result = await getDonorMappingSchema();

      expect(globalThis.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/donor-mapping-schema"),
        expect.objectContaining({
          method: "GET",
        })
      );

      expect(result).toHaveProperty("id");
      expect(result).toHaveProperty("gender");
      expect(result).toHaveProperty("birthDate");
    });

    it("should handle fetch errors", async () => {
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      (globalThis.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        statusText: "Not Found",
      });

      await expect(getDonorMappingSchema()).rejects.toThrow(
        "Failed to fetch donor mapping schema"
      );

      consoleSpy.mockRestore();
    });
  });

  describe("getSampleMappingSchema", () => {
    it("should fetch and normalize sample mapping schema", async () => {
      const mockResponse = {
        id: { required: true },
        material_type: { required: true },
        diagnosis: { required: false },
        diagnosis_date: { required: false },
        collection_date: { required: false },
        storage_temperature: { required: false },
        collection: { required: false },
        donor_id: { required: true },
        sample: { required: true },
      };

      (globalThis.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      const result = await getSampleMappingSchema();

      expect(result).toHaveProperty("id");
      expect(result).toHaveProperty("material_type");
      expect(result).toHaveProperty("diagnosis");
      expect(result.id.saveToPath).toBe("sample_details");
    });

    it("should handle fetch errors", async () => {
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      (globalThis.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        statusText: "Server Error",
      });

      await expect(getSampleMappingSchema()).rejects.toThrow(
        "Failed to fetch sample mapping schema"
      );

      consoleSpy.mockRestore();
    });
  });

  describe("getConditionMappingSchema", () => {
    it("should fetch and normalize condition mapping schema", async () => {
      const mockResponse = {
        "icd-10_code": { required: true },
        patient_id: { required: true },
        diagnosis_date: { required: false },
      };

      (globalThis.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      const result = await getConditionMappingSchema();

      expect(result).toHaveProperty("icd-10_code");
      expect(result).toHaveProperty("patient_id");
      expect(result).toHaveProperty("diagnosis_date");
    });
  });

  describe("getTemperatureValues", () => {
    it("should fetch storage temperature values", async () => {
      const mockResponse = {
        storage_temperature: ["MINUS_80", "MINUS_20", "ROOM_TEMP"],
      };

      (globalThis.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      const result = await getTemperatureValues();

      expect(result).toEqual(["MINUS_80", "MINUS_20", "ROOM_TEMP"]);
    });

    it("should handle fetch errors", async () => {
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      (globalThis.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        statusText: "Error",
      });

      await expect(getTemperatureValues()).rejects.toThrow(
        "Failed to fetch storage temperatures"
      );

      consoleSpy.mockRestore();
    });
  });

  describe("parseDataFromFolder", () => {
    it("should parse JSON file successfully", async () => {
      mockParseMultipleFolderData.mockResolvedValue({
        success: true,
        message: "OK",
        files: [{ content: '{"name": "John", "age": 30}', name: "data.json", ext: ".json" }],
        fileExtension: ".json",
      });

      const result = await parseDataFromFolder("/test/path");

      expect(result.success).toBe(true);
      expect(result.fields).toBeDefined();
      expect(result.fields?.length).toBeGreaterThan(0);
    });

    it("should parse CSV file successfully", async () => {
      mockParseMultipleFolderData.mockResolvedValue({
        success: true,
        message: "OK",
        files: [{ content: "name,age\nJohn,30\nJane,25", name: "data.csv", ext: ".csv" }],
        fileExtension: ".csv",
      });

      const result = await parseDataFromFolder("/test/path");

      expect(result.success).toBe(true);
      expect(result.fields).toBeDefined();
      expect(result.fields?.length).toBe(2);
    });

    it("should parse XML file successfully", async () => {
      mockParseMultipleFolderData.mockResolvedValue({
        success: true,
        message: "OK",
        files: [{ content: "<person><name>John</name><age>30</age></person>", name: "data.xml", ext: ".xml" }],
        fileExtension: ".xml",
      });

      const result = await parseDataFromFolder("/test/path");

      expect(result.success).toBe(true);
      expect(result.fields).toBeDefined();
    });

    it("should handle unsupported file types", async () => {
      mockParseMultipleFolderData.mockResolvedValue({
        success: true,
        message: "OK",
        files: [{ content: "some content", name: "data.txt", ext: ".txt" }],
        fileExtension: ".txt",
      });

      const result = await parseDataFromFolder("/test/path");

      expect(result.success).toBe(false);
      expect(result.message).toContain("No fields could be parsed");
    });

    it("should handle folder not found errors", async () => {
      mockParseMultipleFolderData.mockResolvedValue({
        success: false,
        message: "Folder not found",
        files: [],
      });

      const result = await parseDataFromFolder("/nonexistent");

      expect(result.success).toBe(false);
      expect(result.message).toContain("Folder not found");
    });

    it("should handle parseFolderData errors", async () => {
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      mockParseMultipleFolderData.mockRejectedValue(new Error("File system error"));

      const result = await parseDataFromFolder("/test/path");

      expect(result.success).toBe(false);
      expect(result.message).toContain("File system error");

      consoleSpy.mockRestore();
    });

    it("should handle JSON parsing errors", async () => {
      const consoleSpy = jest.spyOn(console, "warn").mockImplementation();

      mockParseMultipleFolderData.mockResolvedValue({
        success: true,
        message: "OK",
        files: [{ content: "invalid json {", name: "bad.json", ext: ".json" }],
        fileExtension: ".json",
      });

      const result = await parseDataFromFolder("/test/path");

      expect(result.success).toBe(false);
      expect(result.message).toContain("No fields could be parsed");

      consoleSpy.mockRestore();
    });
  });
});
