"use server";

import * as fs from "node:fs";
import * as path from "node:path";
import { XMLParser } from "fast-xml-parser";
import {
  MAX_FILES_TO_PROCESS,
  MAX_ENTRIES_TO_SCAN,
  MAX_TOTAL_READ_BYTES,
} from "@/lib/folder-constants";

type FileType = "json" | "csv" | "xml";

const SAFE_ROOT_FOLDER = process.env.ROOT_DIR || "./../..";

const ACCESS_NOT_ALLOWED_ERROR =
  "Access to the requested folder is not allowed";

export interface ExtractValuesResult {
  success: boolean;
  message: string;
  values?: string[];
  warning?: string;
}

export interface PathExtractionOptions {
  path: string;
  findAnywhere?: boolean;
  iterateSubelements?: boolean;
  selectedAttribute?: string;
}

/**
 * Get common path between two paths
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
 * Validate folder path
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
    throw new Error(`Folder path does not exist: ${folderPath}`);
  }

  const commonPath = getCommonPath(safeRootReal, candidateReal);
  if (commonPath !== safeRootReal) {
    throw new Error(ACCESS_NOT_ALLOWED_ERROR);
  }

  if (!fs.existsSync(candidateReal)) {
    throw new Error(`Folder path does not exist: ${candidateReal}`);
  }

  const stats = fs.statSync(candidateReal);
  if (!stats.isDirectory()) {
    throw new Error(`Path is not a directory: ${candidateReal}`);
  }

  return candidateReal;
}

/**
 * Get value from an object using a dot-separated path
 */
function getValueByPath(obj: unknown, pathStr: string): unknown[] {
  const parts = pathStr.split(".");
  let current: unknown[] = [obj];

  for (const part of parts) {
    const next: unknown[] = [];
    for (const item of current) {
      if (!item || typeof item !== "object") continue;
      const record = item as Record<string, unknown>;
      if (!(part in record)) continue;
      const value = record[part];
      if (Array.isArray(value)) {
        next.push(...value);
      } else {
        next.push(value);
      }
    }
    current = next;
  }

  return current;
}

/**
 * Extract primitive values (strings/numbers) from potentially nested structures
 */
function extractObjectPrimitives(
  record: Record<string, unknown>,
): string[] {
  if ("#text" in record) {
    return [String(record["#text"])];
  }
  const results: string[] = [];
  for (const [key, val] of Object.entries(record)) {
    if (
      !key.startsWith("@") &&
      (typeof val === "string" || typeof val === "number")
    ) {
      results.push(String(val));
    }
  }
  return results;
}

function extractPrimitiveValues(values: unknown[]): string[] {
  const results: string[] = [];

  for (const value of values) {
    if (value === null || value === undefined) {
      continue;
    }
    if (typeof value === "string" || typeof value === "number") {
      results.push(String(value));
    } else if (typeof value === "object") {
      results.push(
        ...extractObjectPrimitives(value as Record<string, unknown>),
      );
    }
  }

  return results;
}

/**
 * Parse JSON file and extract values from paths
 */
function parseJsonAndExtract(content: string, paths: string[]): string[] {
  const data = JSON.parse(content);
  const values: string[] = [];

  const items = Array.isArray(data) ? data : [data];

  for (const item of items) {
    for (const pathStr of paths) {
      const extracted = getValueByPath(item, pathStr);
      values.push(...extractPrimitiveValues(extracted));
    }
  }

  return values;
}

/**
 * Parse CSV file and extract values from paths (column names)
 */
function parseCsvAndExtract(
  content: string,
  paths: string[],
  separator: string = ","
): string[] {
  const lines = content.split("\n").filter((line) => line.trim());
  if (lines.length < 2) return [];

  const headers = lines[0]
    .split(separator)
    .map((h) => h.trim().replaceAll(/['"]/g, ""));

  const values: string[] = [];

  const columnIndices: number[] = [];
  for (const pathStr of paths) {
    const idx = headers.indexOf(pathStr);
    if (idx !== -1) {
      columnIndices.push(idx);
    }
  }

  for (let i = 1; i < lines.length; i++) {
    const row = lines[i]
      .split(separator)
      .map((v) => v.trim().replaceAll(/['"]/g, ""));
    for (const idx of columnIndices) {
      if (row[idx]?.trim()) {
        values.push(row[idx].trim());
      }
    }
  }

  return values;
}

/**
 * Search for a key anywhere in a nested object
 */
function findValueAnywhere(obj: unknown, key: string): unknown[] {
  const results: unknown[] = [];

  function search(current: unknown) {
    if (!current || typeof current !== "object") return;

    if (Array.isArray(current)) {
      for (const item of current) {
        search(item);
      }
    } else {
      const record = current as Record<string, unknown>;
      if (key in record) {
        const value = record[key];
        if (Array.isArray(value)) {
          results.push(...value);
        } else {
          results.push(value);
        }
      }
      for (const val of Object.values(record)) {
        search(val);
      }
    }
  }

  search(obj);
  return results;
}

/**
 * Extract attribute value from objects
 */
function extractAttributeValues(
  values: unknown[],
  attributeName: string
): string[] {
  const results: string[] = [];
  const attrKey = attributeName.startsWith("@")
    ? attributeName
    : `@${attributeName}`;

  for (const value of values) {
    if (value && typeof value === "object") {
      const record = value as Record<string, unknown>;
      if (attrKey in record) {
        const attrValue = record[attrKey];
        if (typeof attrValue === "string" || typeof attrValue === "number") {
          results.push(String(attrValue));
        }
      }
    }
  }

  return results;
}

/**
 * Iterate through all subelements and extract values
 */
function extractFromSubelements(values: unknown[]): string[] {
  const results: string[] = [];

  function extractRecursively(obj: unknown) {
    if (obj === null || obj === undefined) return;

    if (typeof obj === "string" || typeof obj === "number") {
      results.push(String(obj));
      return;
    }

    if (Array.isArray(obj)) {
      for (const item of obj) {
        extractRecursively(item);
      }
      return;
    }

    if (typeof obj === "object") {
      const record = obj as Record<string, unknown>;
      for (const [key, val] of Object.entries(record)) {
        if (!key.startsWith("@")) {
          extractRecursively(val);
        }
      }
    }
  }

  for (const value of values) {
    extractRecursively(value);
  }

  return results;
}

/**
 * Parse XML file and extract values from paths with options
 */
function parseXmlAndExtract(
  content: string,
  pathOptions: PathExtractionOptions[]
): string[] {
  const options = {
    ignoreAttributes: false,
    attributeNamePrefix: "@",
    allowBooleanAttributes: true,
    parseNodeValue: true,
    parseAttributeValue: true,
    trimValues: true,
    parseTrueNumberOnly: false,
    arrayMode: false,
    alwaysCreateTextNode: false,
  };

  const parser = new XMLParser(options);
  const jsonData = parser.parse(content);

  const filtered = filterXmlMetadata(jsonData);

  const values: string[] = [];

  const items = Array.isArray(filtered) ? filtered : [filtered];

  for (const item of items) {
    for (const opt of pathOptions) {
      let extracted: unknown[];

      const pathParts = opt.path.split(".");
      const keyName = pathParts.at(-1)!;

      if (opt.findAnywhere) {
        extracted = findValueAnywhere(item, keyName);
      } else {
        extracted = getValueByPath(item, opt.path);
      }

      if (opt.selectedAttribute?.trim()) {
        values.push(
          ...extractAttributeValues(extracted, opt.selectedAttribute)
        );
      } else if (opt.iterateSubelements) {
        values.push(...extractFromSubelements(extracted));
      } else {
        values.push(...extractPrimitiveValues(extracted));
      }
    }
  }

  return values;
}

function filterXmlMetadata(jsonData: unknown): unknown {
  if (!jsonData || typeof jsonData !== "object") {
    return jsonData;
  }

  const filtered = { ...(jsonData as Record<string, unknown>) };

  delete filtered["?xml"];
  delete filtered["?xml-stylesheet"];
  delete filtered["?xml-model"];

  for (const key of Object.keys(filtered)) {
    if (key.startsWith("?")) {
      delete filtered[key];
    }
  }

  return filtered;
}

interface CollectedFiles {
  dataFiles: string[];
  hasMoreFiles: boolean;
}

function collectDataFiles(
  dirPath: string,
  extension: string,
): CollectedFiles {
  const dataFiles: string[] = [];
  let entriesScanned = 0;
  let hasMoreFiles = false;

  const dir = fs.opendirSync(dirPath);
  try {
    let dirent: fs.Dirent | null;
    while ((dirent = dir.readSync()) !== null) {
      entriesScanned++;
      if (entriesScanned > MAX_ENTRIES_TO_SCAN) {
        hasMoreFiles = true;
        break;
      }
      if (path.extname(dirent.name).toLowerCase() !== extension) continue;
      dataFiles.push(dirent.name);
      if (dataFiles.length >= MAX_FILES_TO_PROCESS) {
        hasMoreFiles = true;
        break;
      }
    }
  } finally {
    dir.closeSync();
  }

  return { dataFiles, hasMoreFiles };
}

function extractFromFileContent(
  content: string,
  fileType: FileType,
  pathOptions: PathExtractionOptions[],
  paths: string[],
  csvSeparator: string,
): string[] {
  if (fileType === "json") return parseJsonAndExtract(content, paths);
  if (fileType === "csv")
    return parseCsvAndExtract(content, paths, csvSeparator);
  if (fileType === "xml") return parseXmlAndExtract(content, pathOptions);
  return [];
}

interface FileProcessingResult {
  values: Set<string>;
  filesRead: number;
  warnings: string[];
}

function processDataFiles(
  dataFiles: string[],
  validatedPath: string,
  fileType: FileType,
  pathOptions: PathExtractionOptions[],
  csvSeparator: string,
): FileProcessingResult {
  const allValues = new Set<string>();
  const paths = pathOptions.map((opt) => opt.path);
  const safeRootReal = fs.realpathSync(SAFE_ROOT_FOLDER);
  const warnings: string[] = [];
  let totalBytesRead = 0;
  let filesRead = 0;

  for (const fileName of dataFiles) {
    const filePath = path.join(validatedPath, fileName);

    let realFilePath: string;
    try {
      realFilePath = fs.realpathSync(filePath);
    } catch {
      continue;
    }

    if (getCommonPath(safeRootReal, realFilePath) !== safeRootReal) continue;

    try {
      const stats = fs.statSync(realFilePath);
      if (totalBytesRead + stats.size > MAX_TOTAL_READ_BYTES) {
        warnings.push(
          `Stopped after reading ${filesRead} files (cumulative size limit of ${Math.round(MAX_TOTAL_READ_BYTES / 1024 / 1024)} MB reached).`,
        );
        break;
      }

      const content = fs.readFileSync(realFilePath, "utf-8");
      totalBytesRead += stats.size;
      filesRead++;

      const extractedValues = extractFromFileContent(
        content,
        fileType,
        pathOptions,
        paths,
        csvSeparator,
      );
      for (const val of extractedValues) {
        const trimmed = val?.trim();
        if (trimmed) allValues.add(trimmed);
      }
    } catch (err) {
      console.error(`Error processing file ${fileName}:`, err);
    }
  }

  return { values: allValues, filesRead, warnings };
}

/**
 * Extract unique values from specified paths across all files in a folder.
 *
 * Guards:
 * - Skips individual files larger than MAX_FILE_SIZE_BYTES (10 MB)
 * - Stops reading once cumulative bytes reach MAX_TOTAL_READ_BYTES (500 MB)
 * - Stops after MAX_FILES_TO_PROCESS files or MAX_ENTRIES_TO_SCAN dir entries
 */
export async function extractValuesFromPaths(
  folderPath: string,
  pathOptions: PathExtractionOptions[],
  fileType: FileType,
  csvSeparator: string = ",",
): Promise<ExtractValuesResult> {
  try {
    if (!pathOptions || pathOptions.length === 0) {
      return { success: false, message: "No paths specified for extraction" };
    }

    const validatedPath = validateFolderPath(folderPath);
    const { dataFiles, hasMoreFiles } = collectDataFiles(
      validatedPath,
      `.${fileType}`,
    );

    if (dataFiles.length === 0) {
      return {
        success: false,
        message: `No ${fileType.toUpperCase()} files found in the folder`,
      };
    }

    const warnings: string[] = [];
    if (hasMoreFiles) {
      warnings.push(
        `The folder may contain more files. Only the first ${dataFiles.length} ${fileType.toUpperCase()} files will be processed.`,
      );
    }

    const result = processDataFiles(
      dataFiles,
      validatedPath,
      fileType,
      pathOptions,
      csvSeparator,
    );
    warnings.push(...result.warnings);

    const uniqueValues = Array.from(result.values).sort((a, b) =>
      a.localeCompare(b),
    );
    return {
      success: true,
      message: `Extracted ${uniqueValues.length} unique values from ${result.filesRead} files`,
      values: uniqueValues,
      warning: warnings.length > 0 ? warnings.join(" ") : undefined,
    };
  } catch (error) {
    const msg =
      error instanceof Error ? error.message : "Failed to extract values";
    console.error("Error extracting values:", error);
    return { success: false, message: msg };
  }
}
