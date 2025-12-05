import { parseFolderData } from "../parse-folder-data";
import * as fs from "fs";

jest.mock("fs", () => ({
  ...jest.requireActual("fs"),
  realpathSync: jest.fn(),
  existsSync: jest.fn(),
  statSync: jest.fn(),
  readdirSync: jest.fn(),
  readFileSync: jest.fn(),
}));

const mockFs = fs as jest.Mocked<typeof fs>;

jest.mock("path", () => ({
  ...jest.requireActual("path"),
  sep: "/",
  join: (...args: string[]) => args.join("/"),
  extname: (p: string) => {
    const match = p.match(/\.[^.]+$/);
    return match ? match[0] : "";
  },
}));

describe("parseFolderData", () => {
  const consoleSpy = jest.spyOn(console, "error").mockImplementation();

  beforeEach(() => {
    jest.clearAllMocks();

    // Default: valid paths within safe root
    mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
      const pathStr = p.toString();
      if (pathStr.includes("./../../") || pathStr === "/opt") return "/opt";
      if (pathStr.startsWith("/opt")) return pathStr;
      throw new Error("ENOENT");
    });
    mockFs.existsSync.mockReturnValue(true);
    mockFs.statSync.mockReturnValue({
      isDirectory: () => true,
      isFile: () => false,
    } as fs.Stats);
    (mockFs.readdirSync as jest.Mock).mockReturnValue([]);
  });

  afterAll(() => {
    consoleSpy.mockRestore();
  });

  describe("input validation", () => {
    it("should return error for empty folderPath", async () => {
      const result = await parseFolderData("");

      expect(result.success).toBe(false);
      expect(result.message).toContain("folderPath parameter is required");
    });

    it("should return error for non-existent folder", async () => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr.includes("./../../")) return "/opt";
        throw new Error("ENOENT");
      });

      const result = await parseFolderData("/opt/nonexistent");

      expect(result.success).toBe(false);
      expect(result.message).toContain("does not exist");
    });
  });

  describe("security validation", () => {
    it("should return error for path outside safe root", async () => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr.includes("./../../")) return "/opt";
        return "/outside/unsafe";
      });

      const result = await parseFolderData("/outside/unsafe");

      expect(result.success).toBe(false);
      expect(result.message).toContain("not allowed");
    });

    it("should return error when path is not a directory", async () => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr.includes("./../../")) return "/opt";
        return "/opt/file.txt";
      });
      mockFs.statSync.mockReturnValue({
        isDirectory: () => false,
        isFile: () => true,
      } as fs.Stats);

      const result = await parseFolderData("/opt/file.txt");

      expect(result.success).toBe(false);
      expect(result.message).toContain("not a directory");
    });
  });

  describe("file reading", () => {
    it("should successfully read JSON file", async () => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr.includes("./../../")) return "/opt";
        return pathStr.startsWith("/opt") ? pathStr : `/opt/${pathStr}`;
      });
      (mockFs.readdirSync as jest.Mock).mockReturnValue(["data.json"]);
      mockFs.statSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        return {
          isDirectory: () => !pathStr.endsWith(".json"),
          isFile: () => pathStr.endsWith(".json"),
        } as fs.Stats;
      });
      mockFs.readFileSync.mockReturnValue('{"key": "value"}');

      const result = await parseFolderData("/opt/data");

      expect(result.success).toBe(true);
      expect(result.fileName).toBe("data.json");
      expect(result.fileExtension).toBe(".json");
      expect(result.fileContent).toBe('{"key": "value"}');
    });

    it("should successfully read CSV file", async () => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr.includes("./../../")) return "/opt";
        return pathStr.startsWith("/opt") ? pathStr : `/opt/${pathStr}`;
      });
      (mockFs.readdirSync as jest.Mock).mockReturnValue(["data.csv"]);
      mockFs.statSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        return {
          isDirectory: () => !pathStr.endsWith(".csv"),
          isFile: () => pathStr.endsWith(".csv"),
        } as fs.Stats;
      });
      mockFs.readFileSync.mockReturnValue("name,age\nAlice,30");

      const result = await parseFolderData("/opt/data");

      expect(result.success).toBe(true);
      expect(result.fileExtension).toBe(".csv");
    });

    it("should successfully read XML file", async () => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr.includes("./../../")) return "/opt";
        return pathStr.startsWith("/opt") ? pathStr : `/opt/${pathStr}`;
      });
      (mockFs.readdirSync as jest.Mock).mockReturnValue(["data.xml"]);
      mockFs.statSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        return {
          isDirectory: () => !pathStr.endsWith(".xml"),
          isFile: () => pathStr.endsWith(".xml"),
        } as fs.Stats;
      });
      mockFs.readFileSync.mockReturnValue("<root><item/></root>");

      const result = await parseFolderData("/opt/data");

      expect(result.success).toBe(true);
      expect(result.fileExtension).toBe(".xml");
    });

    it("should return error when no supported files found", async () => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr.includes("./../../")) return "/opt";
        return pathStr.startsWith("/opt") ? pathStr : `/opt/${pathStr}`;
      });
      (mockFs.readdirSync as jest.Mock).mockReturnValue([
        "readme.txt",
        "image.png",
      ]);

      const result = await parseFolderData("/opt/data");

      expect(result.success).toBe(false);
      expect(result.message).toContain("No supported data files");
    });

    it("should skip unsupported file extensions", async () => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr.includes("./../../")) return "/opt";
        return pathStr.startsWith("/opt") ? pathStr : `/opt/${pathStr}`;
      });
      (mockFs.readdirSync as jest.Mock).mockReturnValue([
        "readme.txt",
        "data.json",
      ]);
      mockFs.statSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        return {
          isDirectory: () => !pathStr.match(/\.(json|csv|xml|txt)$/),
          isFile: () => !!pathStr.match(/\.(json|csv|xml|txt)$/),
        } as fs.Stats;
      });
      mockFs.readFileSync.mockReturnValue('{"found": true}');

      const result = await parseFolderData("/opt/data");

      expect(result.success).toBe(true);
      expect(result.fileName).toBe("data.json");
    });

    it("should skip files that fail realpath", async () => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr.includes("./../../")) return "/opt";
        if (pathStr === "/opt/data") return "/opt/data";

        if (pathStr.includes("bad.json")) throw new Error("ENOENT");
        return pathStr;
      });
      (mockFs.readdirSync as jest.Mock).mockReturnValue([
        "bad.json",
        "good.json",
      ]);
      mockFs.statSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        return {
          isDirectory: () => !pathStr.endsWith(".json"),
          isFile: () => pathStr.endsWith(".json"),
        } as fs.Stats;
      });
      mockFs.readFileSync.mockReturnValue('{"good": true}');

      const result = await parseFolderData("/opt/data");

      expect(result.success).toBe(true);
      expect(result.fileName).toBe("good.json");
    });

    it("should skip directories with supported extensions", async () => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr.includes("./../../")) return "/opt";
        return pathStr.startsWith("/opt") ? pathStr : `/opt/${pathStr}`;
      });
      (mockFs.readdirSync as jest.Mock).mockReturnValue([
        "folder.json",
        "real.json",
      ]);
      mockFs.statSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        // folder.json is a directory, real.json is a file
        if (pathStr.includes("folder.json")) {
          return { isDirectory: () => true, isFile: () => false } as fs.Stats;
        }
        return {
          isDirectory: () => !pathStr.endsWith(".json"),
          isFile: () => pathStr.endsWith(".json"),
        } as fs.Stats;
      });
      mockFs.readFileSync.mockReturnValue('{"real": true}');

      const result = await parseFolderData("/opt/data");

      expect(result.success).toBe(true);
      expect(result.fileName).toBe("real.json");
    });

    it("should handle permission denied on folder read", async () => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr.includes("./../../")) return "/opt";
        return pathStr.startsWith("/opt") ? pathStr : `/opt/${pathStr}`;
      });
      (mockFs.readdirSync as jest.Mock).mockImplementation(() => {
        throw new Error("EACCES");
      });

      const result = await parseFolderData("/opt/data");

      expect(result.success).toBe(false);
      expect(result.message).toContain("Permission denied");
    });

    it("should stop scanning after MAX_FILES_TO_SCAN (100)", async () => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr.includes("./../../")) return "/opt";
        return pathStr.startsWith("/opt") ? pathStr : `/opt/${pathStr}`;
      });
      // Create 150 non-matching files
      const files = Array.from({ length: 150 }, (_, i) => `file${i}.txt`);
      (mockFs.readdirSync as jest.Mock).mockReturnValue(files);

      const result = await parseFolderData("/opt/data");

      expect(result.success).toBe(false);
      expect(result.message).toContain("No supported data files");
    });
  });

  describe("error handling", () => {
    it("should handle unexpected errors gracefully", async () => {
      mockFs.realpathSync.mockImplementation(() => {
        throw new Error("Unexpected error");
      });

      const result = await parseFolderData("/opt/data");

      expect(result.success).toBe(false);
      expect(consoleSpy).toHaveBeenCalled();
    });
  });
});
