import { getFolders } from "@/actions/folder/folder-actions";

// Mock the global fetch function
globalThis.fetch = jest.fn();

describe("getFolders", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should fetch folders successfully with default parameters", async () => {
    const mockResponse = {
      entries: [
        { name: "folder1", path: "/folder1", isDirectory: true },
        { name: "folder2", path: "/folder2", isDirectory: true },
      ],
    };

    (globalThis.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await getFolders();

    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/list-directories"),
      expect.objectContaining({
        method: "GET",
        headers: { "Content-Type": "application/json" },
      })
    );
    expect(result).toEqual(mockResponse.entries);
  });

  it("should fetch folders with custom path", async () => {
    const mockResponse = {
      entries: [
        { name: "subfolder", path: "/folder/subfolder", isDirectory: true },
      ],
    };

    (globalThis.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await getFolders("/folder");

    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("path=%2Ffolder"),
      expect.any(Object)
    );
    expect(result).toEqual(mockResponse.entries);
  });

  it("should include files when includeFiles is true", async () => {
    const mockResponse = {
      entries: [
        { name: "file.txt", path: "/file.txt", isDirectory: false },
        { name: "folder", path: "/folder", isDirectory: true },
      ],
    };

    (globalThis.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await getFolders("", true);

    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("include_files=true"),
      expect.any(Object)
    );
    expect(result).toEqual(mockResponse.entries);
  });

  it("should handle HTTP errors", async () => {
    const consoleSpy = jest.spyOn(console, "error").mockImplementation();

    (globalThis.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 404,
      statusText: "Not Found",
      json: jest.fn().mockResolvedValue({ error: "Folder not found" }),
    });

    await expect(getFolders("/nonexistent")).rejects.toThrow(
      "Failed to fetch folders"
    );

    consoleSpy.mockRestore();
  });

  it("should handle invalid response format", async () => {
    const consoleSpy = jest.spyOn(console, "error").mockImplementation();

    (globalThis.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue({ invalid: "response" }),
    });

    await expect(getFolders()).rejects.toThrow(
      "Invalid response format from FHIR module API"
    );

    consoleSpy.mockRestore();
  });

  it("should handle network errors", async () => {
    const consoleSpy = jest.spyOn(console, "error").mockImplementation();

    (globalThis.fetch as jest.Mock).mockRejectedValue(
      new Error("Network error")
    );

    await expect(getFolders()).rejects.toThrow("Failed to fetch folders");

    consoleSpy.mockRestore();
  });
});
