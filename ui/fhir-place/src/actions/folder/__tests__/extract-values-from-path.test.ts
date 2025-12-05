import {
  extractValuesFromPaths,
  PathExtractionOptions,
} from "../extract-values-from-path";
import * as fs from "fs";

// Mock the fs module
jest.mock("fs");
const mockFs = jest.mocked(fs);

// Mock path.sep for cross-platform compatibility
jest.mock("path", () => ({
  ...jest.requireActual("path"),
  sep: "/",
  join: (...args: string[]) => args.join("/"),
  extname: (p: string) => {
    const match = p.match(/\.[^.]+$/);
    return match ? match[0] : "";
  },
}));

// Helper to mock readdirSync - it returns string[] when withFileTypes is not used
const mockReadDir = (files: string[]) => {
  (mockFs.readdirSync as jest.Mock).mockReturnValue(files);
};

describe("extractValuesFromPaths", () => {
  const consoleSpy = jest.spyOn(console, "error").mockImplementation();

  beforeEach(() => {
    jest.clearAllMocks();

    // Setup default mock implementations
    mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
      const pathStr = p.toString();
      if (pathStr === "./../.." || pathStr === "/opt") {
        return "/opt";
      }
      if (pathStr.startsWith("/opt")) {
        return pathStr;
      }
      throw new Error(`Path does not exist: ${pathStr}`);
    });

    mockFs.existsSync.mockReturnValue(true);
    mockFs.statSync.mockReturnValue({ isDirectory: () => true } as fs.Stats);
    (mockFs.readdirSync as jest.Mock).mockReturnValue([]);
  });

  afterAll(() => {
    consoleSpy.mockRestore();
  });

  describe("input validation", () => {
    it("should return error when no paths are specified", async () => {
      const result = await extractValuesFromPaths("/opt/data", [], "json");

      expect(result.success).toBe(false);
      expect(result.message).toBe("No paths specified for extraction");
    });

    it("should return error when pathOptions is empty array", async () => {
      const result = await extractValuesFromPaths("/opt/data", [], "csv");

      expect(result.success).toBe(false);
      expect(result.message).toBe("No paths specified for extraction");
    });
  });

  describe("folder validation", () => {
    it("should return error for non-existent folder", async () => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr === "./../.." || pathStr === "/opt") {
          return "/opt";
        }
        throw new Error(`Folder path does not exist: ${pathStr}`);
      });

      const pathOptions: PathExtractionOptions[] = [{ path: "name" }];
      const result = await extractValuesFromPaths(
        "/opt/nonexistent",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(false);
      expect(result.message).toContain("Folder path does not exist");
    });

    it("should return error when path is outside safe root", async () => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr === "./../.." || pathStr === "/opt") {
          return "/opt";
        }
        if (pathStr === "/outside/data") {
          return "/outside/data";
        }
        throw new Error(`Path does not exist: ${pathStr}`);
      });

      const pathOptions: PathExtractionOptions[] = [{ path: "name" }];
      const result = await extractValuesFromPaths(
        "/outside/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(false);
      expect(result.message).toContain(
        "Access to the requested folder is not allowed"
      );
    });

    it("should return error when path is not a directory", async () => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr === "./../.." || pathStr === "/opt") {
          return "/opt";
        }
        return pathStr;
      });
      mockFs.statSync.mockReturnValue({ isDirectory: () => false } as fs.Stats);

      const pathOptions: PathExtractionOptions[] = [{ path: "name" }];
      const result = await extractValuesFromPaths(
        "/opt/file.txt",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(false);
      expect(result.message).toContain("Path is not a directory");
    });
  });

  describe("file discovery", () => {
    it("should return error when no files of specified type exist", async () => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr === "./../.." || pathStr === "/opt") {
          return "/opt";
        }
        return pathStr;
      });
      mockReadDir(["file1.txt", "file2.csv"]);

      const pathOptions: PathExtractionOptions[] = [{ path: "name" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(false);
      expect(result.message).toBe("No JSON files found in the folder");
    });

    it("should return warning when more than 100 files are found", async () => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr === "./../.." || pathStr === "/opt") {
          return "/opt";
        }
        return pathStr;
      });

      // Create 150 files
      const files = Array.from({ length: 150 }, (_, i) => `file${i}.json`);
      mockReadDir(files);
      mockFs.readFileSync.mockReturnValue('{"name": "test"}');

      const pathOptions: PathExtractionOptions[] = [{ path: "name" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(true);
      expect(result.warning).toContain("150 files");
      expect(result.warning).toContain("100 files will be processed");
    });
  });

  describe("JSON extraction", () => {
    beforeEach(() => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr === "./../.." || pathStr === "/opt") {
          return "/opt";
        }
        return pathStr;
      });
    });

    it("should extract simple values from JSON files", async () => {
      mockReadDir(["data1.json", "data2.json"]);
      mockFs.readFileSync
        .mockReturnValueOnce('{"name": "Alice"}')
        .mockReturnValueOnce('{"name": "Bob"}');

      const pathOptions: PathExtractionOptions[] = [{ path: "name" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("Alice");
      expect(result.values).toContain("Bob");
      expect(result.values?.length).toBe(2);
    });

    it("should extract nested values from JSON files", async () => {
      mockReadDir(["data.json"]);
      mockFs.readFileSync.mockReturnValue(
        '{"person": {"name": "Charlie", "address": {"city": "NYC"}}}'
      );

      const pathOptions: PathExtractionOptions[] = [
        { path: "person.address.city" },
      ];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("NYC");
    });

    it("should extract values from JSON arrays", async () => {
      mockReadDir(["data.json"]);
      mockFs.readFileSync.mockReturnValue(
        '[{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}]'
      );

      const pathOptions: PathExtractionOptions[] = [{ path: "name" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("Alice");
      expect(result.values).toContain("Bob");
      expect(result.values).toContain("Charlie");
    });

    it("should extract array values from JSON", async () => {
      mockReadDir(["data.json"]);
      mockFs.readFileSync.mockReturnValue('{"tags": ["red", "green", "blue"]}');

      const pathOptions: PathExtractionOptions[] = [{ path: "tags" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("red");
      expect(result.values).toContain("green");
      expect(result.values).toContain("blue");
    });

    it("should handle numeric values in JSON", async () => {
      mockReadDir(["data.json"]);
      mockFs.readFileSync.mockReturnValue('{"count": 42, "price": 19.99}');

      const pathOptions: PathExtractionOptions[] = [
        { path: "count" },
        { path: "price" },
      ];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("42");
      expect(result.values).toContain("19.99");
    });

    it("should return unique values from JSON", async () => {
      mockReadDir(["data1.json", "data2.json"]);
      mockFs.readFileSync
        .mockReturnValueOnce('{"status": "active"}')
        .mockReturnValueOnce('{"status": "active"}');

      const pathOptions: PathExtractionOptions[] = [{ path: "status" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(true);
      expect(result.values).toEqual(["active"]);
    });

    it("should handle JSON parsing errors gracefully", async () => {
      mockReadDir(["valid.json", "invalid.json"]);
      mockFs.readFileSync
        .mockReturnValueOnce('{"name": "valid"}')
        .mockReturnValueOnce("not valid json {");

      const pathOptions: PathExtractionOptions[] = [{ path: "name" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("valid");
      expect(consoleSpy).toHaveBeenCalled();
    });

    it("should skip null and undefined values in JSON", async () => {
      mockReadDir(["data.json"]);
      mockFs.readFileSync.mockReturnValue(
        '{"name": "test", "empty": null, "items": [null, "value", null]}'
      );

      const pathOptions: PathExtractionOptions[] = [
        { path: "name" },
        { path: "empty" },
        { path: "items" },
      ];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("test");
      expect(result.values).toContain("value");
      expect(result.values?.length).toBe(2);
    });
  });

  describe("CSV extraction", () => {
    beforeEach(() => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr === "./../.." || pathStr === "/opt") {
          return "/opt";
        }
        return pathStr;
      });
    });

    it("should extract values from CSV columns", async () => {
      mockReadDir(["data.csv"]);
      mockFs.readFileSync.mockReturnValue(
        "name,age,city\nAlice,30,NYC\nBob,25,LA"
      );

      const pathOptions: PathExtractionOptions[] = [{ path: "name" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "csv"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("Alice");
      expect(result.values).toContain("Bob");
    });

    it("should extract multiple columns from CSV", async () => {
      mockReadDir(["data.csv"]);
      mockFs.readFileSync.mockReturnValue(
        "name,age,city\nAlice,30,NYC\nBob,25,LA"
      );

      const pathOptions: PathExtractionOptions[] = [
        { path: "name" },
        { path: "city" },
      ];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "csv"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("Alice");
      expect(result.values).toContain("Bob");
      expect(result.values).toContain("NYC");
      expect(result.values).toContain("LA");
    });

    it("should use custom CSV separator", async () => {
      mockReadDir(["data.csv"]);
      mockFs.readFileSync.mockReturnValue(
        "name;age;city\nAlice;30;NYC\nBob;25;LA"
      );

      const pathOptions: PathExtractionOptions[] = [{ path: "name" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "csv",
        ";"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("Alice");
      expect(result.values).toContain("Bob");
    });

    it("should handle quoted values in CSV", async () => {
      mockReadDir(["data.csv"]);
      mockFs.readFileSync.mockReturnValue(
        '"name","age"\n"Alice Smith","30"\n"Bob Jones","25"'
      );

      const pathOptions: PathExtractionOptions[] = [{ path: "name" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "csv"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("Alice Smith");
      expect(result.values).toContain("Bob Jones");
    });

    it("should return empty when CSV column not found", async () => {
      mockReadDir(["data.csv"]);
      mockFs.readFileSync.mockReturnValue("name,age\nAlice,30\nBob,25");

      const pathOptions: PathExtractionOptions[] = [
        { path: "nonexistent_column" },
      ];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "csv"
      );

      expect(result.success).toBe(true);
      expect(result.values).toEqual([]);
    });

    it("should handle empty CSV files gracefully", async () => {
      mockReadDir(["data.csv"]);
      mockFs.readFileSync.mockReturnValue("name,age");

      const pathOptions: PathExtractionOptions[] = [{ path: "name" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "csv"
      );

      expect(result.success).toBe(true);
      expect(result.values).toEqual([]);
    });

    it("should skip empty values in CSV", async () => {
      mockReadDir(["data.csv"]);
      mockFs.readFileSync.mockReturnValue("name,age\nAlice,30\n,25\nBob,");

      const pathOptions: PathExtractionOptions[] = [{ path: "name" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "csv"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("Alice");
      expect(result.values).toContain("Bob");
      expect(result.values?.length).toBe(2);
    });
  });

  describe("XML extraction", () => {
    beforeEach(() => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr === "./../.." || pathStr === "/opt") {
          return "/opt";
        }
        return pathStr;
      });
    });

    it("should extract simple values from XML", async () => {
      mockReadDir(["data.xml"]);
      mockFs.readFileSync.mockReturnValue(
        '<?xml version="1.0"?><root><name>Alice</name></root>'
      );

      const pathOptions: PathExtractionOptions[] = [{ path: "root.name" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "xml"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("Alice");
    });

    it("should extract nested values from XML", async () => {
      mockReadDir(["data.xml"]);
      mockFs.readFileSync.mockReturnValue(
        "<root><person><address><city>NYC</city></address></person></root>"
      );

      const pathOptions: PathExtractionOptions[] = [
        { path: "root.person.address.city" },
      ];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "xml"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("NYC");
    });

    it("should extract attribute values from XML", async () => {
      mockReadDir(["data.xml"]);
      mockFs.readFileSync.mockReturnValue(
        '<root><item id="123" status="active">Value</item></root>'
      );

      const pathOptions: PathExtractionOptions[] = [
        { path: "root.item", selectedAttribute: "id" },
      ];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "xml"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("123");
    });

    it("should extract attribute with @ prefix", async () => {
      mockReadDir(["data.xml"]);
      mockFs.readFileSync.mockReturnValue(
        '<root><item id="456">Value</item></root>'
      );

      const pathOptions: PathExtractionOptions[] = [
        { path: "root.item", selectedAttribute: "@id" },
      ];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "xml"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("456");
    });

    it("should find values anywhere in XML when findAnywhere is true", async () => {
      mockReadDir(["data.xml"]);
      mockFs.readFileSync.mockReturnValue(
        "<root><level1><level2><target>found</target></level2></level1></root>"
      );

      const pathOptions: PathExtractionOptions[] = [
        { path: "target", findAnywhere: true },
      ];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "xml"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("found");
    });

    it("should extract from subelements when iterateSubelements is true", async () => {
      mockReadDir(["data.xml"]);
      mockFs.readFileSync.mockReturnValue(
        "<root><container><a>val1</a><b>val2</b><c>val3</c></container></root>"
      );

      const pathOptions: PathExtractionOptions[] = [
        { path: "root.container", iterateSubelements: true },
      ];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "xml"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("val1");
      expect(result.values).toContain("val2");
      expect(result.values).toContain("val3");
    });

    it("should filter XML metadata from results", async () => {
      mockReadDir(["data.xml"]);
      mockFs.readFileSync.mockReturnValue(
        '<?xml version="1.0" encoding="UTF-8"?><?xml-stylesheet type="text/xsl"?><root><name>test</name></root>'
      );

      const pathOptions: PathExtractionOptions[] = [{ path: "root.name" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "xml"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("test");
      expect(result.values?.some((v) => v.includes("xml"))).toBe(false);
    });

    it("should handle XML with text content (#text)", async () => {
      mockReadDir(["data.xml"]);
      mockFs.readFileSync.mockReturnValue(
        '<root><item attr="x">text content</item></root>'
      );

      const pathOptions: PathExtractionOptions[] = [{ path: "root.item" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "xml"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("text content");
    });

    it("should handle XML parsing errors gracefully", async () => {
      mockReadDir(["valid.xml", "invalid.xml"]);
      mockFs.readFileSync
        .mockReturnValueOnce("<root><name>valid</name></root>")
        .mockReturnValueOnce("<invalid><unclosed>");

      const pathOptions: PathExtractionOptions[] = [{ path: "root.name" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "xml"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("valid");
    });
  });

  describe("edge cases", () => {
    beforeEach(() => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr === "./../.." || pathStr === "/opt") {
          return "/opt";
        }
        return pathStr;
      });
    });

    it("should sort extracted values alphabetically", async () => {
      mockReadDir(["data.json"]);
      mockFs.readFileSync.mockReturnValue(
        '[{"name": "Charlie"}, {"name": "Alice"}, {"name": "Bob"}]'
      );

      const pathOptions: PathExtractionOptions[] = [{ path: "name" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(true);
      expect(result.values).toEqual(["Alice", "Bob", "Charlie"]);
    });

    it("should handle empty string path", async () => {
      mockReadDir(["data.json"]);
      mockFs.readFileSync.mockReturnValue('{"name": "test"}');

      const pathOptions: PathExtractionOptions[] = [{ path: "" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(true);
    });

    it("should handle deeply nested paths", async () => {
      mockReadDir(["data.json"]);
      mockFs.readFileSync.mockReturnValue(
        '{"a": {"b": {"c": {"d": {"e": "deep"}}}}}'
      );

      const pathOptions: PathExtractionOptions[] = [{ path: "a.b.c.d.e" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("deep");
    });

    it("should handle file read errors gracefully", async () => {
      mockReadDir(["readable.json", "unreadable.json"]);
      mockFs.readFileSync
        .mockReturnValueOnce('{"name": "readable"}')
        .mockImplementationOnce(() => {
          throw new Error("Permission denied");
        });

      const pathOptions: PathExtractionOptions[] = [{ path: "name" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("readable");
      expect(consoleSpy).toHaveBeenCalled();
    });

    it("should skip files outside safe root during iteration", async () => {
      mockReadDir(["data.json"]);

      let callCount = 0;
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr === "./../.." || pathStr === "/opt") {
          return "/opt";
        }
        // First call for folder validation returns /opt/data
        if (pathStr === "/opt/data") {
          return "/opt/data";
        }
        // File path check returns outside safe root
        callCount++;
        if (callCount === 1) {
          return "/opt/data"; // folder check
        }
        return "/outside/data.json"; // file path outside safe root
      });

      const pathOptions: PathExtractionOptions[] = [{ path: "name" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(true);
      expect(result.values).toEqual([]);
    });

    it("should trim whitespace from extracted values", async () => {
      mockReadDir(["data.json"]);
      mockFs.readFileSync.mockReturnValue('{"name": "  trimmed  "}');

      const pathOptions: PathExtractionOptions[] = [{ path: "name" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("trimmed");
    });

    it("should skip empty trimmed values", async () => {
      mockReadDir(["data.json"]);
      mockFs.readFileSync.mockReturnValue('{"name": "valid", "empty": "   "}');

      const pathOptions: PathExtractionOptions[] = [
        { path: "name" },
        { path: "empty" },
      ];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("valid");
      expect(result.values?.length).toBe(1);
    });
  });

  describe("multiple files", () => {
    beforeEach(() => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr === "./../.." || pathStr === "/opt") {
          return "/opt";
        }
        return pathStr;
      });
    });

    it("should aggregate unique values from multiple JSON files", async () => {
      mockReadDir(["file1.json", "file2.json", "file3.json"]);
      mockFs.readFileSync
        .mockReturnValueOnce('{"type": "A"}')
        .mockReturnValueOnce('{"type": "B"}')
        .mockReturnValueOnce('{"type": "A"}');

      const pathOptions: PathExtractionOptions[] = [{ path: "type" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(true);
      expect(result.values).toEqual(["A", "B"]);
      expect(result.message).toContain("2 unique values");
      expect(result.message).toContain("3 files");
    });

    it("should aggregate values from multiple CSV files", async () => {
      mockReadDir(["file1.csv", "file2.csv"]);
      mockFs.readFileSync
        .mockReturnValueOnce("status\nactive\npending")
        .mockReturnValueOnce("status\ncompleted\nactive");

      const pathOptions: PathExtractionOptions[] = [{ path: "status" }];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "csv"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("active");
      expect(result.values).toContain("pending");
      expect(result.values).toContain("completed");
      expect(result.values?.length).toBe(3);
    });
  });

  describe("multiple paths extraction", () => {
    beforeEach(() => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr === "./../.." || pathStr === "/opt") {
          return "/opt";
        }
        return pathStr;
      });
    });

    it("should extract values from multiple paths", async () => {
      mockReadDir(["data.json"]);
      mockFs.readFileSync.mockReturnValue(
        '{"firstName": "John", "lastName": "Doe", "age": 30}'
      );

      const pathOptions: PathExtractionOptions[] = [
        { path: "firstName" },
        { path: "lastName" },
      ];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "json"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("John");
      expect(result.values).toContain("Doe");
    });

    it("should combine XML options with different extraction modes", async () => {
      mockReadDir(["data.xml"]);
      mockFs.readFileSync.mockReturnValue(
        '<root><item id="1">value1</item><nested><target>value2</target></nested></root>'
      );

      const pathOptions: PathExtractionOptions[] = [
        { path: "root.item", selectedAttribute: "id" },
        { path: "target", findAnywhere: true },
      ];
      const result = await extractValuesFromPaths(
        "/opt/data",
        pathOptions,
        "xml"
      );

      expect(result.success).toBe(true);
      expect(result.values).toContain("1");
      expect(result.values).toContain("value2");
    });
  });
});
