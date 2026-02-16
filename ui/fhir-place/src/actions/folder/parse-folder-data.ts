"use server";

import * as fs from "fs";
import * as path from "path";
import { MAX_FILES_TO_SCAN, SUPPORTED_EXTENSIONS } from "@/lib/folder-constants";

const SAFE_ROOT_FOLDER = process.env.ROOT_DIR || "./../../";

const ACCESS_NOT_ALLOWED_ERROR =
  "Access to the requested folder is not allowed";

export interface ParseFolderResult {
  success: boolean;
  message: string;
  fileContent?: string;
  fileName?: string;
  fileExtension?: string;
}

export interface DataFileInfo {
  content: string;
  name: string;
  ext: string;
}

export interface ParseMultipleFilesResult {
  success: boolean;
  message: string;
  files: DataFileInfo[];
  fileExtension?: string;
}

/**
 * Validate folder path from request content.
 * Limits access to a safe root directory.
 */
function validateFolderPath(folderPath: string): string {
  if (!folderPath || typeof folderPath !== "string") {
    throw new Error("folderPath parameter is required");
  }

  const safeRootReal = fs.realpathSync(SAFE_ROOT_FOLDER);
  let candidateReal: string;

  try {
    candidateReal = fs.realpathSync(folderPath);
  } catch {
    throw new Error(`Folder path does not exist: ${escapeHtml(folderPath)}`);
  }

  try {
    const commonPath = getCommonPath(safeRootReal, candidateReal);
    if (commonPath !== safeRootReal) {
      throw new Error(ACCESS_NOT_ALLOWED_ERROR);
    }
  } catch {
    throw new Error(ACCESS_NOT_ALLOWED_ERROR);
  }

  if (!fs.existsSync(candidateReal)) {
    throw new Error(`Folder path does not exist: ${escapeHtml(candidateReal)}`);
  }

  const stats = fs.statSync(candidateReal);
  if (!stats.isDirectory()) {
    throw new Error(`Path is not a directory: ${escapeHtml(candidateReal)}`);
  }

  return candidateReal;
}

/**
 * Get common path between two paths (similar to Python's os.path.commonpath)
 */
function getCommonPath(path1: string, path2: string): string {
  const parts1 = path1.split(path.sep);
  const parts2 = path2.split(path.sep);
  const common: string[] = [];

  for (let i = 0; i < Math.min(parts1.length, parts2.length); i++) {
    if (parts1[i] === parts2[i]) {
      common.push(parts1[i]);
    } else {
      break;
    }
  }

  return common.join(path.sep);
}


/**
 * Find and read the first supported data file from a folder.
 * Uses opendirSync to iterate without loading all entries into memory.
 * Limited to scanning MAX_FILES_TO_SCAN files to prevent performance issues.
 */
function readFirstDataFile(folderPath: string): {
  content: string;
  name: string;
  ext: string;
} {
  const safeRootReal = fs.realpathSync(SAFE_ROOT_FOLDER);
  const normalizedPath = fs.realpathSync(folderPath);

  const folderCommonPath = getCommonPath(safeRootReal, normalizedPath);
  if (folderCommonPath !== safeRootReal) {
    throw new Error(ACCESS_NOT_ALLOWED_ERROR);
  }

  let dir: fs.Dir;
  try {
    dir = fs.opendirSync(folderPath);
  } catch {
    throw new Error("Permission denied accessing folder");
  }

  let scannedCount = 0;

  try {
    let dirent: fs.Dirent | null;
    while ((dirent = dir.readSync()) !== null) {
      if (scannedCount >= MAX_FILES_TO_SCAN) {
        break;
      }
      scannedCount++;

      const fileName = dirent.name;
      const ext = path.extname(fileName).toLowerCase();
      if (!SUPPORTED_EXTENSIONS.includes(ext)) {
        continue;
      }

      const filePath = path.join(folderPath, fileName);
      let realFilePath: string;

      try {
        realFilePath = fs.realpathSync(filePath);
      } catch {
        continue;
      }

      const fileCommonPath = getCommonPath(normalizedPath, realFilePath);
      if (fileCommonPath !== normalizedPath) {
        continue;
      }

      try {
        const stats = fs.statSync(realFilePath);
        if (!stats.isFile()) {
          continue;
        }

        const content = fs.readFileSync(realFilePath, "utf-8");
        return {
          content,
          name: fileName,
          ext: ext,
        };
      } catch {
        continue;
      }
    }
  } finally {
    dir.closeSync();
  }

  throw new Error(
    `No supported data files found in ${escapeHtml(
      folderPath
    )}. Supported formats: JSON, CSV, XML`
  );
}

/**
 * Find and read up to MAX_FILES_TO_SCAN supported data files from a folder.
 * Uses opendirSync to iterate without loading all entries into memory.
 * All files must be of the same type (extension).
 */
function readMultipleDataFiles(folderPath: string): DataFileInfo[] {
  const safeRootReal = fs.realpathSync(SAFE_ROOT_FOLDER);
  const normalizedPath = fs.realpathSync(folderPath);

  const folderCommonPath = getCommonPath(safeRootReal, normalizedPath);
  if (folderCommonPath !== safeRootReal) {
    throw new Error(ACCESS_NOT_ALLOWED_ERROR);
  }

  let dir: fs.Dir;
  try {
    dir = fs.opendirSync(folderPath);
  } catch {
    throw new Error("Permission denied accessing folder");
  }

  const files: DataFileInfo[] = [];
  let scannedCount = 0;
  let targetExt: string | null = null;

  try {
    let dirent: fs.Dirent | null;
    while ((dirent = dir.readSync()) !== null) {
      if (scannedCount >= MAX_FILES_TO_SCAN) {
        break;
      }
      scannedCount++;

      const fileName = dirent.name;
      const ext = path.extname(fileName).toLowerCase();
      if (!SUPPORTED_EXTENSIONS.includes(ext)) {
        continue;
      }

      // Only collect files of the same type as the first found
      if (targetExt === null) {
        targetExt = ext;
      } else if (ext !== targetExt) {
        continue;
      }

      const filePath = path.join(folderPath, fileName);
      let realFilePath: string;

      try {
        realFilePath = fs.realpathSync(filePath);
      } catch {
        continue;
      }

      const fileCommonPath = getCommonPath(normalizedPath, realFilePath);
      if (fileCommonPath !== normalizedPath) {
        continue;
      }

      try {
        const stats = fs.statSync(realFilePath);
        if (!stats.isFile()) {
          continue;
        }

        const content = fs.readFileSync(realFilePath, "utf-8");
        files.push({
          content,
          name: fileName,
          ext: ext,
        });
      } catch {
        continue;
      }
    }
  } finally {
    dir.closeSync();
  }

  return files;
}

/**
 * Simple HTML escape function to prevent XSS in error messages
 */
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Get file content from a folder for frontend parsing.
 * This replaces the Python /parse-folder-data endpoint.
 */
export async function parseFolderData(
  folderPath: string
): Promise<ParseFolderResult> {
  try {
    const validatedPath = validateFolderPath(folderPath);
    const { content, name, ext } = readFirstDataFile(validatedPath);

    return {
      success: true,
      message: `Successfully read ${name} (first file found)`,
      fileContent: content,
      fileName: name,
      fileExtension: ext,
    };
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Internal server error";
    console.error("Error in parseFolderData:", message);
    return {
      success: false,
      message,
    };
  }
}

/**
 * Get file contents from multiple files in a folder for parsing.
 * Reads up to MAX_FILES_TO_SCAN files of the same type.
 */
export async function parseMultipleFolderData(
  folderPath: string
): Promise<ParseMultipleFilesResult> {
  try {
    const validatedPath = validateFolderPath(folderPath);
    const files = readMultipleDataFiles(validatedPath);

    if (files.length === 0) {
      return {
        success: false,
        message: `No supported data files found in ${escapeHtml(
          folderPath
        )}. Supported formats: JSON, CSV, XML`,
        files: [],
      };
    }

    return {
      success: true,
      message: `Successfully read ${files.length} file(s)`,
      files,
      fileExtension: files[0].ext,
    };
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Internal server error";
    console.error("Error in parseMultipleFolderData:", message);
    return {
      success: false,
      message,
      files: [],
    };
  }
}
