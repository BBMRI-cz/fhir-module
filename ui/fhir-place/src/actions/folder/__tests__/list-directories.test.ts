import {
  listDirectories,
  getFolders,
  getRootFolderInfo,
} from "../list-directories";
import * as fs from "node:fs";

// Mock the fs module with explicit opendirSync
jest.mock("fs", () => ({
  ...jest.requireActual("fs"),
  realpathSync: jest.fn(),
  existsSync: jest.fn(),
  statSync: jest.fn(),
  opendirSync: jest.fn(),
}));

const mockFs = fs as jest.Mocked<typeof fs>;

jest.mock("path", () => ({
  ...jest.requireActual("path"),
  sep: "/",
  join: (...args: string[]) => args.join("/"),
  basename: (p: string) => p.split("/").pop() || "",
}));

// Mock Dirent class for opendirSync
const createMockDirent = (name: string, isDir: boolean): fs.Dirent =>
  ({
    name,
    isDirectory: () => isDir,
    isFile: () => !isDir,
    isBlockDevice: () => false,
    isCharacterDevice: () => false,
    isFIFO: () => false,
    isSocket: () => false,
    isSymbolicLink: () => false,
    path: "",
    parentPath: "",
  } as fs.Dirent);

// Helper to create a mock Dir object
const createMockDir = (entries: fs.Dirent[]) => {
  let idx = 0;
  return {
    readSync: jest.fn(() => entries[idx++] || null),
    closeSync: jest.fn(),
  };
};

describe("list-directories", () => {
  const consoleSpy = jest.spyOn(console, "error").mockImplementation();

  beforeEach(() => {
    jest.clearAllMocks();

    // Default mocks
    mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
      const pathStr = p.toString();
      if (pathStr.includes("test")) return "/opt/test";
      if (pathStr === "/") return "/opt/test";
      if (pathStr.startsWith("/opt")) return pathStr;
      return `/opt/test${pathStr}`;
    });
    mockFs.existsSync.mockReturnValue(true);
    mockFs.statSync.mockReturnValue({ isDirectory: () => true } as fs.Stats);
    mockFs.opendirSync.mockReturnValue(createMockDir([]) as unknown as fs.Dir);
  });

  afterAll(() => {
    consoleSpy.mockRestore();
  });

  describe("listDirectories", () => {
    it("should list directories in root path", async () => {
      const mockDir = createMockDir([
        createMockDirent("folder1", true),
        createMockDirent("folder2", true),
      ]);
      mockFs.opendirSync.mockReturnValue(mockDir as unknown as fs.Dir);

      const result = await listDirectories("/");

      expect(result.entries).toHaveLength(2);
      expect(result.entries[0].name).toBe("folder1");
      expect(result.entries[0].isDirectory).toBe(true);
    });

    it("should include files when includeFiles is true", async () => {
      const mockDir = createMockDir([
        createMockDirent("folder", true),
        createMockDirent("file.txt", false),
      ]);
      mockFs.opendirSync.mockReturnValue(mockDir as unknown as fs.Dir);

      const result = await listDirectories("/", true);

      expect(result.entries).toHaveLength(2);
      expect(result.entries.some((e) => e.name === "file.txt")).toBe(true);
    });

    it("should limit files to MAX_FILES_LIMIT (10) and add placeholder", async () => {
      const entries = [
        createMockDirent("dir", true),
        ...Array.from({ length: 15 }, (_, i) =>
          createMockDirent(`file${i}.txt`, false)
        ),
      ];
      mockFs.opendirSync.mockReturnValue(
        createMockDir(entries) as unknown as fs.Dir
      );

      const result = await listDirectories("/", true);

      // 1 dir + 10 files + 1 placeholder = 12
      expect(result.entries).toHaveLength(12);
      expect(result.hasMoreFiles).toBe(true);
      expect(result.entries.at(-1)!.isPlaceholder).toBe(
        true
      );
    });

    it("should throw error for path outside allowed directory", async () => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr.includes("test")) return "/opt/test";
        return "/outside/path";
      });

      await expect(listDirectories("/outside")).rejects.toThrow(
        "Access denied"
      );
    });

    it("should throw error for non-directory path", async () => {
      mockFs.realpathSync.mockImplementation((p: fs.PathLike) => {
        const pathStr = p.toString();
        if (pathStr.includes("test")) return "/opt/test";
        return "/opt/test/file.txt";
      });
      mockFs.statSync.mockReturnValue({ isDirectory: () => false } as fs.Stats);

      await expect(listDirectories("/opt/test/file.txt")).rejects.toThrow(
        "not a directory"
      );
    });

    it("should sort entries alphabetically", async () => {
      const mockDir = createMockDir([
        createMockDirent("zebra", true),
        createMockDirent("alpha", true),
        createMockDirent("beta", true),
      ]);
      mockFs.opendirSync.mockReturnValue(mockDir as unknown as fs.Dir);

      const result = await listDirectories("/");

      expect(result.entries.map((e) => e.name)).toEqual([
        "alpha",
        "beta",
        "zebra",
      ]);
    });
  });

  describe("getFolders", () => {
    it("should return FolderTreeRecord array", async () => {
      mockFs.opendirSync.mockReturnValue(
        createMockDir([createMockDirent("folder", true)]) as unknown as fs.Dir
      );

      const result = await getFolders("/");

      expect(result).toHaveLength(1);
      expect(result[0]).toHaveProperty("name", "folder");
      expect(result[0]).toHaveProperty("path");
      expect(result[0]).toHaveProperty("isDirectory", true);
    });

    it("should handle errors gracefully", async () => {
      mockFs.realpathSync.mockImplementation(() => {
        throw new Error("Test error");
      });

      await expect(getFolders("/")).rejects.toThrow("Failed to fetch folders");
    });
  });

  describe("getRootFolderInfo", () => {
    it("should return root folder info", async () => {
      mockFs.realpathSync.mockReturnValue("/opt/data");

      const result = await getRootFolderInfo();

      expect(result.name).toBe("data");
      expect(result.path).toBe("/opt/data");
      expect(result.isDirectory).toBe(true);
    });

    it("should handle errors gracefully", async () => {
      mockFs.realpathSync.mockImplementation(() => {
        throw new Error("Cannot resolve");
      });

      await expect(getRootFolderInfo()).rejects.toThrow(
        "Failed to get root folder info"
      );
    });
  });
});
