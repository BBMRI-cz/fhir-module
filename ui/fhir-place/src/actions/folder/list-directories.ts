"use server";

import * as fs from "fs";
import * as path from "path";
import { FolderTreeRecord } from "@/types/actions/folder/types";
import {
  MAX_FILES_LIMIT,
  MAX_ENTRIES_TO_SCAN,
} from "@/lib/folder-constants";

const SAFE_ROOT_FOLDER = process.env.ROOT_DIR || "../../test/";

interface DirectoryEntry {
  name: string;
  path: string;
  isDirectory: boolean;
  isPlaceholder?: boolean;
}

interface ListDirectoriesResult {
  path: string;
  entries: DirectoryEntry[];
  hasMoreFiles?: boolean;
  totalFilesCount?: number;
}

function validateDirectoryPath(baseDir: string, relativePath: string): string {
  let targetPath: string;

  if (relativePath === "/") {
    targetPath = baseDir;
  } else {
    targetPath = relativePath;
  }

  const realPath = fs.realpathSync(targetPath);
  const realBaseDir = fs.realpathSync(baseDir);

  if (
    !realPath.startsWith(realBaseDir + path.sep) &&
    realPath !== realBaseDir
  ) {
    throw new Error("Access denied: path outside allowed directory");
  }

  if (!fs.existsSync(realPath)) {
    throw new Error("Path does not exist");
  }

  const stats = fs.statSync(realPath);
  if (!stats.isDirectory()) {
    throw new Error("Path is not a directory");
  }

  return realPath;
}

interface BuildEntriesResult {
  entries: DirectoryEntry[];
  hasMoreFiles: boolean;
  totalFilesCount: number;
}

/**
 * Build list of directory entries with metadata.
 * Returns all directories but limits files to MAX_FILES_LIMIT.
 * Uses fs.opendirSync to iterate without loading all entries into memory.
 * Stops scanning after MAX_ENTRIES_TO_SCAN to prevent freezing on huge directories.
 */
function buildDirectoryEntries(
  dirPath: string,
  relativePath: string,
  baseDir: string,
  includeFiles: boolean
): BuildEntriesResult {
  const directories: DirectoryEntry[] = [];
  const files: DirectoryEntry[] = [];

  const dir = fs.opendirSync(dirPath);
  let hasMoreFiles = false;
  let entriesScanned = 0;

  try {
    let dirent: fs.Dirent | null;
    while ((dirent = dir.readSync()) !== null) {
      entriesScanned++;

      if (entriesScanned > MAX_ENTRIES_TO_SCAN) {
        hasMoreFiles = true;
        break;
      }

      const entryName = dirent.name;
      const entryPath = path.join(dirPath, entryName);

      try {
        if (dirent.isDirectory()) {
          directories.push({
            name: entryName,
            path: entryPath,
            isDirectory: true,
          });
        } else if (includeFiles) {
          if (files.length < MAX_FILES_LIMIT) {
            files.push({
              name: entryName,
              path: entryPath,
              isDirectory: false,
            });
          } else {
            hasMoreFiles = true;
          }
        }
      } catch {
        continue;
      }
    }
  } finally {
    dir.closeSync();
  }

  directories.sort((a, b) =>
    a.name.toLowerCase().localeCompare(b.name.toLowerCase())
  );

  files.sort((a, b) =>
    a.name.toLowerCase().localeCompare(b.name.toLowerCase())
  );

  if (hasMoreFiles) {
    files.push({
      name: "...",
      path: "",
      isDirectory: false,
      isPlaceholder: true,
    });
  }

  const entries = [...directories, ...files];

  return { entries, hasMoreFiles, totalFilesCount: files.length };
}

/**
 * List directories inside the container.
 * Supports optional path parameter to list subdirectories.
 * Returns all directories but limits files to MAX_FILES_LIMIT.
 */
export async function listDirectories(
  folderPath: string = "/",
  includeFiles: boolean = false
): Promise<ListDirectoriesResult> {
  try {
    const baseDir = fs.realpathSync(SAFE_ROOT_FOLDER);
    const targetPath = folderPath || "/";

    const resolvedPath = validateDirectoryPath(baseDir, targetPath);
    const { entries, hasMoreFiles, totalFilesCount } = buildDirectoryEntries(
      resolvedPath,
      targetPath,
      baseDir,
      includeFiles
    );

    return {
      path: resolvedPath,
      entries,
      hasMoreFiles,
      totalFilesCount,
    };
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : "Unknown error";
    throw new Error(`Failed to list directories: ${errorMessage}`);
  }
}

/**
 * Get folders as FolderTreeRecord array.
 * This is a convenience wrapper that maintains compatibility with existing code.
 * Returns all directories but limits files to MAX_FILES_LIMIT with a placeholder for more.
 */
export async function getFolders(
  folderPath: string = "",
  includeFiles: boolean = false
): Promise<FolderTreeRecord[]> {
  try {
    const targetPath = folderPath || "/";
    const result = await listDirectories(targetPath, includeFiles);

    return result.entries.map((entry) => ({
      name: entry.name,
      path: entry.path,
      isDirectory: entry.isDirectory,
      isPlaceholder: entry.isPlaceholder,
    }));
  } catch (err) {
    console.error("Error listing directories:", err);
    throw new Error(`Failed to fetch folders: ${(err as Error).message}`);
  }
}

/**
 * Get the root folder info as a FolderTreeRecord.
 * This allows the root folder itself to be selectable in the UI.
 */
export async function getRootFolderInfo(): Promise<FolderTreeRecord> {
  try {
    const baseDir = fs.realpathSync(SAFE_ROOT_FOLDER);
    const name = path.basename(baseDir) || "Root";

    return {
      name,
      path: baseDir,
      isDirectory: true,
    };
  } catch (err) {
    console.error("Error getting root folder info:", err);
    throw new Error(
      `Failed to get root folder info: ${(err as Error).message}`
    );
  }
}
