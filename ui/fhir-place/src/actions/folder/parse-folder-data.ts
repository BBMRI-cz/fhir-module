"use server";

import * as fs from "fs";
import * as path from "path";

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

const MAX_FILES_TO_SCAN = 50;
const SUPPORTED_EXTENSIONS = [".json", ".csv", ".xml"];

/**
 * Find and read the first supported data file from a folder.
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

  let files: string[];
  try {
    files = fs.readdirSync(folderPath);
  } catch {
    throw new Error("Permission denied accessing folder");
  }

  let scannedCount = 0;

  for (const fileName of files) {
    if (scannedCount >= MAX_FILES_TO_SCAN) {
      break;
    }
    scannedCount++;

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

  throw new Error(
    `No supported data files found in ${escapeHtml(
      folderPath
    )}. Supported formats: JSON, CSV, XML`
  );
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
