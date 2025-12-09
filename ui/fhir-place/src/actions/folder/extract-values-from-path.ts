"use server";

import * as fs from "fs";
import * as path from "path";
import { XMLParser } from "fast-xml-parser";
import {
  MAX_FILES_TO_PROCESS,
  MAX_ENTRIES_TO_SCAN,
} from "@/lib/folder-constants";

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
      if (item && typeof item === "object") {
        const record = item as Record<string, unknown>;
        if (part in record) {
          const value = record[part];
          if (Array.isArray(value)) {
            next.push(...value);
          } else {
            next.push(value);
          }
        }
      }
    }
    current = next;
  }

  return current;
}

/**
 * Extract primitive values (strings/numbers) from potentially nested structures
 */
function extractPrimitiveValues(values: unknown[]): string[] {
  const results: string[] = [];

  for (const value of values) {
    if (value === null || value === undefined) {
      continue;
    }
    if (typeof value === "string" || typeof value === "number") {
      results.push(String(value));
    } else if (typeof value === "object") {
      const record = value as Record<string, unknown>;
      if ("#text" in record) {
        results.push(String(record["#text"]));
      } else {
        for (const [key, val] of Object.entries(record)) {
          if (
            !key.startsWith("@") &&
            (typeof val === "string" || typeof val === "number")
          ) {
            results.push(String(val));
          }
        }
      }
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
      if (row[idx] && row[idx].trim()) {
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
      const keyName = pathParts[pathParts.length - 1];

      if (opt.findAnywhere) {
        extracted = findValueAnywhere(item, keyName);
      } else {
        extracted = getValueByPath(item, opt.path);
      }

      if (opt.selectedAttribute && opt.selectedAttribute.trim()) {
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

/**
 * Extract unique values from specified paths across all files in a folder
 */
export async function extractValuesFromPaths(
  folderPath: string,
  pathOptions: PathExtractionOptions[],
  fileType: "json" | "csv" | "xml",
  csvSeparator: string = ","
): Promise<ExtractValuesResult> {
  try {
    if (!pathOptions || pathOptions.length === 0) {
      return {
        success: false,
        message: "No paths specified for extraction",
      };
    }

    const validatedPath = validateFolderPath(folderPath);
    const extension = `.${fileType}`;

    // Use opendirSync to iterate without loading all entries into memory
    const dataFiles: string[] = [];
    let entriesScanned = 0;
    let hasMoreFiles = false;

    const dir = fs.opendirSync(validatedPath);
    try {
      let dirent: fs.Dirent | null;
      while ((dirent = dir.readSync()) !== null) {
        entriesScanned++;

        // Stop scanning if we've hit the limit to prevent freezing on huge directories
        if (entriesScanned > MAX_ENTRIES_TO_SCAN) {
          hasMoreFiles = true;
          break;
        }

        const fileName = dirent.name;
        if (path.extname(fileName).toLowerCase() !== extension) {
          continue;
        }

        dataFiles.push(fileName);

        // Stop collecting files once we have enough
        if (dataFiles.length >= MAX_FILES_TO_PROCESS) {
          hasMoreFiles = true;
          break;
        }
      }
    } finally {
      dir.closeSync();
    }

    if (dataFiles.length === 0) {
      return {
        success: false,
        message: `No ${fileType.toUpperCase()} files found in the folder`,
      };
    }

    let warning: string | undefined;
    if (hasMoreFiles) {
      warning = `The folder may contain more files. Only the first ${dataFiles.length} ${fileType.toUpperCase()} files will be processed.`;
    }

    const allValues: Set<string> = new Set();

    const paths = pathOptions.map((opt) => opt.path);

    for (const fileName of dataFiles) {
      const filePath = path.join(validatedPath, fileName);

      const safeRootReal = fs.realpathSync(SAFE_ROOT_FOLDER);
      const realFilePath = fs.realpathSync(filePath);
      const commonPath = getCommonPath(safeRootReal, realFilePath);
      if (commonPath !== safeRootReal) {
        continue;
      }

      try {
        const content = fs.readFileSync(realFilePath, "utf-8");
        let extractedValues: string[] = [];

        if (fileType === "json") {
          extractedValues = parseJsonAndExtract(content, paths);
        } else if (fileType === "csv") {
          extractedValues = parseCsvAndExtract(content, paths, csvSeparator);
        } else if (fileType === "xml") {
          extractedValues = parseXmlAndExtract(content, pathOptions);
        }

        for (const val of extractedValues) {
          if (val && val.trim()) {
            allValues.add(val.trim());
          }
        }
      } catch (err) {
        console.error(`Error processing file ${fileName}:`, err);
      }
    }

    const uniqueValues = Array.from(allValues).sort();

    return {
      success: true,
      message: `Extracted ${uniqueValues.length} unique values from ${dataFiles.length} files`,
      values: uniqueValues,
      warning,
    };
  } catch (error) {
    console.error("Error extracting values:", error);
    return {
      success: false,
      message:
        error instanceof Error ? error.message : "Failed to extract values",
    };
  }
}
