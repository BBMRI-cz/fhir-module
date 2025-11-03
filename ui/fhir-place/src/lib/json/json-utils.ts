import { get, set } from "lodash-es";
import {
  DataMappingRecord,
  DataRecord,
  EnumMapping,
} from "@/types/setup-wizard/types";
import { DataField } from "@/types/actions/configuration-details/types";

const xmlMappingRules: Record<string, { dependsOn: string }> = {
  sample_details: {
    dependsOn: "sample",
  },
};

export const mapEnumMappingToJson = (mappings: EnumMapping[]): string => {
  return JSON.stringify(
    mappings.reduce((acc, mapping) => {
      acc[mapping.userValue] = mapping.apiValue;
      return acc;
    }, {} as Record<string, string>),
    null,
    2
  );
};

export function validateEnumJson(
  enumObject: object,
  availableOptions: string[]
): { valid: boolean; error?: string } {
  for (const [key, val] of Object.entries(enumObject)) {
    if (typeof key !== "string" || typeof val !== "string") {
      return {
        valid: false,
        error: "JSON must contain only string key-value pairs",
      };
    }

    if (key.trim() === "" || val.trim() === "") {
      return { valid: false, error: "Keys and values cannot be empty strings" };
    }

    if (availableOptions.length > 0 && !availableOptions.includes(val)) {
      return {
        valid: false,
        error: `Value "${val}" is not an available option`,
      };
    }
  }

  return { valid: true };
}

interface ParseResult {
  valid: boolean;
  error?: string;
  record?: Record<string, DataMappingRecord[]>;
}

interface PathInfo {
  path: string;
  attribute: string | null;
  findAnywhere: boolean;
  iterateSubelements: boolean;
}

// Extract path parsing logic
function parsePathString(value: string): PathInfo {
  let path = value;
  let attribute = null;
  let findAnywhere = false;
  let iterateSubelements = false;

  // Handle findAnywhere flag
  if (value.startsWith("**.")) {
    findAnywhere = true;
    path = value.substring(3);
  }

  // Handle iterate subelements flag
  if (path.endsWith(".*")) {
    iterateSubelements = true;
    path = path.substring(0, path.length - 2);
  }

  // Handle attribute selection
  if (path.includes("@")) {
    const parts = path.split("@");
    path = parts[0];
    if (path.endsWith(".")) {
      path = path.slice(0, -1);
    }
    attribute = `@${parts[1]}`;
  }

  return {
    path: path.trim(),
    attribute,
    findAnywhere,
    iterateSubelements,
  };
}

// Find matching data field
function findDataField(
  pathInfo: PathInfo,
  availablePaths: DataField[]
): DataField | undefined {
  if (pathInfo.findAnywhere) {
    return availablePaths.find((p) => {
      const lastPart = p.path.trim().split(".").pop();
      return lastPart === pathInfo.path;
    });
  }

  return availablePaths.find((p) => p.path === pathInfo.path);
}

// Create mapping records for path candidates with attributes
function createPathCandidateRecords(
  key: string,
  pathInfo: PathInfo,
  pathCandidates: string[],
  availablePaths: DataField[],
  mappingRecord: Record<string, DataMappingRecord[]>
): void {
  const viablePathValues = availablePaths
    .filter((p) => pathCandidates.includes(p.path))
    .filter((p) => p.attributes?.includes(pathInfo.attribute!));

  mappingRecord[key] = mappingRecord[key] || [];
  mappingRecord[key].push(
    ...viablePathValues.map((p) => ({
      value: p.path,
      findAnywhere: pathInfo.findAnywhere,
      iterateSubelements: pathInfo.iterateSubelements,
      selectedAttribute: pathInfo.attribute || undefined,
    }))
  );
}

// Validate path and attribute
function validatePathAndAttribute(
  pathInfo: PathInfo,
  pathValue: DataField | undefined
): { valid: boolean; error?: string } {
  if (!pathValue) {
    return {
      valid: false,
      error: `Path "${pathInfo.path}" is not available`,
    };
  }

  if (
    pathInfo.attribute &&
    !pathValue.attributes?.includes(pathInfo.attribute)
  ) {
    return {
      valid: false,
      error: `Attribute "${pathInfo.attribute}" is not available`,
    };
  }

  return { valid: true };
}

// Process a single value string
function processSingleValue(
  key: string,
  value: string,
  availablePaths: DataField[],
  pathCandidates: string[],
  mappingRecord: Record<string, DataMappingRecord[]>
): { valid: boolean; error?: string } {
  const pathInfo = parsePathString(value);

  // Handle path candidates with attributes
  if (pathCandidates.length && pathInfo.attribute) {
    createPathCandidateRecords(
      key,
      pathInfo,
      pathCandidates,
      availablePaths,
      mappingRecord
    );
    return { valid: true };
  }

  // Find and validate the data field
  const pathValue = findDataField(pathInfo, availablePaths);
  const validation = validatePathAndAttribute(pathInfo, pathValue);

  if (!validation.valid) {
    return validation;
  }

  // Create the mapping record
  const singleRecord: DataMappingRecord = {
    value: pathValue!.path,
    ...(pathInfo.findAnywhere && { findAnywhere: true }),
    ...(pathInfo.iterateSubelements && { iterateSubelements: true }),
    ...(pathInfo.attribute && { selectedAttribute: pathInfo.attribute }),
  };

  mappingRecord[key] = mappingRecord[key] || [];
  mappingRecord[key].push(singleRecord);

  return { valid: true };
}

// Process array of values (split by " || ")
function processValues(
  key: string,
  valueString: string,
  availablePaths: DataField[],
  pathCandidates: string[],
  mappingRecord: Record<string, DataMappingRecord[]>
): { valid: boolean; error?: string } {
  const values = valueString.split(" || ");

  for (const value of values) {
    const result = processSingleValue(
      key,
      value,
      availablePaths,
      pathCandidates,
      mappingRecord
    );
    if (!result.valid) {
      return result;
    }
  }

  return { valid: true };
}

// Get parent path for wildcard resolution
function getParentPath(
  parentKey: string | undefined,
  originalJson: object | undefined
): string | undefined {
  if (!parentKey || !originalJson) return undefined;

  const dependsOnKey = xmlMappingRules[parentKey]?.dependsOn;
  return dependsOnKey ? get(originalJson, dependsOnKey) : undefined;
}

// Main function - now much cleaner
export function parseJsonToMappingRecord(
  parsedJson: object,
  availablePaths: DataField[],
  parentKey?: string,
  originalJson?: object
): ParseResult {
  const mappingRecord: Record<string, DataMappingRecord[]> = {};

  // Resolve parent path and candidates
  const parentPath = getParentPath(parentKey, originalJson);
  const pathCandidates = parentPath
    ? resolveMatchingRecordsForWildcardPaths(
        parentPath,
        availablePaths.map((p) => p.path)
      )
    : [];

  // Process each key-value pair
  for (const [key, value] of Object.entries(parsedJson)) {
    // Skip empty values
    if (!value || value === "") {
      continue;
    }

    // Handle nested objects recursively
    if (typeof value === "object") {
      const result = parseJsonToMappingRecord(
        value,
        availablePaths,
        key,
        parsedJson
      );
      if (!result.valid) {
        return result;
      }

      // Merge nested results
      for (const [k, v] of Object.entries(result.record!)) {
        mappingRecord[k] = v;
      }
      continue;
    }

    // Process string values
    const result = processValues(
      key,
      value,
      availablePaths,
      pathCandidates,
      mappingRecord
    );
    if (!result.valid) {
      return result;
    }
  }

  return { valid: true, record: mappingRecord };
}

function resolveMatchingRecordsForWildcardPaths(
  stringPath: string,
  availablePaths: string[]
): string[] {
  const validPaths: string[] = [];
  const paths = stringPath.split(" || ");

  for (const path of paths) {
    const corePath = path.replace("**.", "").replace(".*", "");
    const findAnywhere = path.startsWith("**.");
    const iterateSubelements = path.endsWith(".*");

    let pathCandidates = [...availablePaths];
    if (findAnywhere) {
      pathCandidates = pathCandidates.filter((p) => p.includes(corePath));
    }

    if (iterateSubelements) {
      pathCandidates = pathCandidates.filter((p) => {
        const parts = p.split(".");
        const coreIndex = parts.indexOf(corePath);

        if (coreIndex === -1 || coreIndex === parts.length - 1) {
          return false;
        }

        return coreIndex === parts.length - 2;
      });
    }

    validPaths.push(...pathCandidates);
  }

  return validPaths;
}

// Process path relative to XML parent dependency
function processXmlDependentPath(
  path: string,
  parentRecord: DataMappingRecord
): string {
  if (!path.startsWith(parentRecord.value)) {
    return path;
  }

  let result = path.substring(parentRecord.value.length);

  if (result.startsWith(".")) {
    result = result.substring(1);
  }

  if (parentRecord.iterateSubelements) {
    const dotIndex = result.indexOf(".");
    result = dotIndex === -1 ? "" : result.substring(dotIndex + 1);
  }

  return result;
}

// Apply XML parent dependency transformation to path
function applyXmlDependency(
  path: string,
  record: DataRecord,
  allData: Record<string, DataRecord>
): string {
  if (record.xmlDependsOn === undefined) {
    return path;
  }

  const parent = allData[record.xmlDependsOn];
  for (const parentRecord of parent.mappings) {
    const processedPath = processXmlDependentPath(path, parentRecord);
    if (processedPath !== path) {
      return processedPath;
    }
  }

  return path;
}

// Extract the last component of the path for findAnywhere
function extractFindAnywherePath(path: string): string {
  const parts = path.split(".");
  return parts.at(-1)!;
}

// Build the final path string with modifiers
function buildPathString(
  path: string,
  findAnywhere: boolean,
  selectedAttribute: string | undefined,
  iterateSubelements: boolean
): string {
  const prefix = findAnywhere ? "**." : "";
  const attribute = selectedAttribute ? `.${selectedAttribute}` : "";
  const suffix = iterateSubelements ? ".*" : "";

  let result = `${prefix}${path}${attribute}${suffix}`;

  // Clean up leading/trailing dots
  if (result.startsWith(".")) {
    result = result.slice(1);
  }
  if (result.endsWith(".")) {
    result = result.slice(0, -1);
  }

  return result;
}

// Process a single mapping record into a path string
function processMappingRecord(
  mapping: DataMappingRecord,
  record: DataRecord,
  allData: Record<string, DataRecord>
): string {
  const { value, findAnywhere, iterateSubelements, selectedAttribute } =
    mapping;

  let path = applyXmlDependency(value, record, allData);

  if (findAnywhere) {
    path = extractFindAnywherePath(path);
  }

  return buildPathString(
    path,
    findAnywhere ?? false,
    selectedAttribute,
    iterateSubelements ?? false
  );
}

// Build JSON path with optional result path prefix
function buildJsonPath(key: string, resultPath: string | undefined): string {
  return resultPath ? `${resultPath}.${key}` : key;
}

// Process all mappings for a single data record
function processMappings(
  record: DataRecord,
  allData: Record<string, DataRecord>
): string[] {
  return record.mappings.map((mapping) =>
    processMappingRecord(mapping, record, allData)
  );
}

// Main export function - now with much lower complexity
export function mappingRecordToJson(
  data: Record<string, DataRecord>,
  filterEmpty: boolean = false
): string {
  const result: Record<string, string> = {};

  for (const key in data) {
    const parts = processMappings(data[key], data);
    const value = [...new Set(parts)].join(" || ");

    if (filterEmpty && value === "") {
      continue;
    }

    const jsonPath = buildJsonPath(key, data[key].resultPath);
    set(result, jsonPath, value);
  }

  return JSON.stringify(result, null, 2);
}
