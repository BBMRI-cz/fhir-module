"use server";

import * as fs from "node:fs";
import * as path from "node:path";
import {
  MAX_FILES_TO_SCAN,
  MAX_FILES_FOR_SCHEMA,
  MAX_TOTAL_READ_BYTES,
  SUPPORTED_EXTENSIONS,
} from "@/lib/folder-constants";

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

  let candidateReal: string;

  try {
    candidateReal = fs.realpathSync(folderPath);
  } catch {
    throw new Error(`Folder path does not exist: ${escapeHtml(folderPath)}`);
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
 * Limited to scanning MAX_FILES_TO_SCAN entries to prevent performance issues.
 */
function readFirstDataFile(folderPath: string): {
  content: string;
  name: string;
  ext: string;
} {
  const normalizedPath = fs.realpathSync(folderPath);

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

interface CandidateFile {
  name: string;
  ext: string;
}

/**
 * Scan the directory and collect candidate file names filtered by extension.
 * All returned files share the same extension (the first supported one found).
 */
function scanDirectoryForCandidates(
  folderPath: string,
  maxFiles: number,
): CandidateFile[] {
  const dir = fs.opendirSync(folderPath);
  const candidates: CandidateFile[] = [];
  let scannedCount = 0;
  let targetExt: string | null = null;

  try {
    let dirent: fs.Dirent | null;
    while ((dirent = dir.readSync()) !== null) {
      if (scannedCount >= MAX_FILES_TO_SCAN) break;
      scannedCount++;
      if (candidates.length >= maxFiles) break;

      const ext = path.extname(dirent.name).toLowerCase();
      if (!SUPPORTED_EXTENSIONS.includes(ext)) continue;

      if (targetExt === null) {
        targetExt = ext;
      } else if (ext !== targetExt) {
        continue;
      }

      candidates.push({ name: dirent.name, ext });
    }
  } finally {
    dir.closeSync();
  }

  return candidates;
}

/** Resolve and validate that a file path stays within the allowed directory. */
function resolveValidFilePath(
  fileName: string,
  folderPath: string,
  normalizedPath: string,
): string | null {
  const filePath = path.join(folderPath, fileName);
  try {
    const realFilePath = fs.realpathSync(filePath);
    if (getCommonPath(normalizedPath, realFilePath) !== normalizedPath)
      return null;
    return realFilePath;
  } catch {
    return null;
  }
}

/** Read validated candidate files, respecting the cumulative size budget. */
function readValidatedFiles(
  candidates: CandidateFile[],
  folderPath: string,
  normalizedPath: string,
): DataFileInfo[] {
  const files: DataFileInfo[] = [];
  let totalBytesRead = 0;

  for (const candidate of candidates) {
    const realFilePath = resolveValidFilePath(
      candidate.name,
      folderPath,
      normalizedPath,
    );
    if (!realFilePath) continue;

    try {
      const stats = fs.statSync(realFilePath);
      if (!stats.isFile()) continue;
      if (totalBytesRead + stats.size > MAX_TOTAL_READ_BYTES) break;

      const content = fs.readFileSync(realFilePath, "utf-8");
      totalBytesRead += stats.size;
      files.push({ content, name: candidate.name, ext: candidate.ext });
    } catch {
      continue;
    }
  }

  return files;
}

/**
 * Find and read supported data files from a folder.
 * Uses opendirSync to iterate without loading all entries into memory.
 * All files must be of the same type (extension).
 *
 * Stops when either limit is reached first:
 * - File count reaches maxFiles
 * - Cumulative bytes read reaches MAX_TOTAL_READ_BYTES
 *
 * @param folderPath - Validated absolute folder path
 * @param maxFiles - Maximum number of files to read (defaults to MAX_FILES_TO_SCAN)
 */
function readMultipleDataFiles(
  folderPath: string,
  maxFiles: number = MAX_FILES_TO_SCAN,
): DataFileInfo[] {
  const normalizedPath = fs.realpathSync(folderPath);

  let candidates: CandidateFile[];
  try {
    candidates = scanDirectoryForCandidates(folderPath, maxFiles);
  } catch {
    throw new Error("Permission denied accessing folder");
  }

  return readValidatedFiles(candidates, folderPath, normalizedPath);
}

/**
 * Simple HTML escape function to prevent XSS in error messages
 */
function escapeHtml(text: string): string {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
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
 * Get file contents from multiple files in a folder for schema discovery.
 * Reads only a small sample (MAX_FILES_FOR_SCHEMA) since we only need field names,
 * not every record. Skips files larger than MAX_FILE_SIZE_BYTES.
 */
export async function parseMultipleFolderData(
  folderPath: string
): Promise<ParseMultipleFilesResult> {
  try {
    const validatedPath = validateFolderPath(folderPath);
    const files = readMultipleDataFiles(validatedPath, MAX_FILES_FOR_SCHEMA);

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
