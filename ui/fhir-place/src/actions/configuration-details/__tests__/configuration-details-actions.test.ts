import {
  getDonorMappingSchema,
  getSampleMappingSchema,
  getConditionMappingSchema,
  getTemperatureValues,
  parseDataFromFolder,
} from "@/actions/configuration-details/configuration-details-actions";

// Mock fetch globally
globalThis.fetch = jest.fn();

describe("configuration-details-actions", () => {
  beforeEach(() => {
    jest.clearAllMocks();
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
      const mockResponse = {
        success: true,
        fileContent: '{"name": "John", "age": 30}',
        fileExtension: ".json",
        fileName: "data.json",
      };

      (globalThis.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      const result = await parseDataFromFolder("/test/path");

      expect(result.success).toBe(true);
      expect(result.fields).toBeDefined();
      expect(result.fields?.length).toBeGreaterThan(0);
    });

    it("should parse CSV file successfully", async () => {
      const mockResponse = {
        success: true,
        fileContent: "name,age\nJohn,30\nJane,25",
        fileExtension: ".csv",
        fileName: "data.csv",
      };

      (globalThis.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      const result = await parseDataFromFolder("/test/path");

      expect(result.success).toBe(true);
      expect(result.fields).toBeDefined();
      expect(result.fields?.length).toBe(2);
    });

    it("should parse XML file successfully", async () => {
      const mockResponse = {
        success: true,
        fileContent: "<person><name>John</name><age>30</age></person>",
        fileExtension: ".xml",
        fileName: "data.xml",
      };

      (globalThis.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      const result = await parseDataFromFolder("/test/path");

      expect(result.success).toBe(true);
      expect(result.fields).toBeDefined();
    });

    it("should handle unsupported file types", async () => {
      const mockResponse = {
        success: true,
        fileContent: "some content",
        fileExtension: ".txt",
        fileName: "data.txt",
      };

      (globalThis.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      const result = await parseDataFromFolder("/test/path");

      expect(result.success).toBe(false);
      expect(result.message).toContain("Unsupported file type");
    });

    it("should handle backend errors", async () => {
      (globalThis.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 404,
        statusText: "Not Found",
        json: jest.fn().mockResolvedValue({ message: "Folder not found" }),
      });

      const result = await parseDataFromFolder("/nonexistent");

      expect(result.success).toBe(false);
      expect(result.message).toContain("Folder not found");
    });

    it("should handle network errors", async () => {
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      (globalThis.fetch as jest.Mock).mockRejectedValue(
        new Error("Network error")
      );

      const result = await parseDataFromFolder("/test/path");

      expect(result.success).toBe(false);
      expect(result.message).toContain("Network error");

      consoleSpy.mockRestore();
    });

    it("should handle JSON parsing errors", async () => {
      const mockResponse = {
        success: true,
        fileContent: "invalid json {",
        fileExtension: ".json",
        fileName: "bad.json",
      };

      (globalThis.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      const result = await parseDataFromFolder("/test/path");

      expect(result.success).toBe(false);
      expect(result.message).toContain("Error parsing");
    });
  });
});
