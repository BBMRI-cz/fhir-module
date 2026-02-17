"use server";

/* eslint-disable @typescript-eslint/no-explicit-any */
import { XMLParser } from "fast-xml-parser";
import {
  ConditionMap,
  DonorMap,
  SampleMap,
  SimpleKeyInfo,
  ParsedDataResult,
  DataField,
} from "@/types/actions/configuration-details/types";
import { parseMultipleFolderData } from "@/actions/folder/parse-folder-data";
const BASE_URL = process.env.BACKEND_API_URL || "http://localhost:5000";

// ---------------------------------------------------------------------------
// Generic in-memory cache (module-level, persists for the process lifetime)
// ---------------------------------------------------------------------------
const CACHE_DURATION_MINUTES = 60;

interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

const cache = new Map<string, CacheEntry<unknown>>();

function getCached<T>(key: string): T | null {
  const entry = cache.get(key);
  if (
    entry &&
    (Date.now() - entry.timestamp) / 1000 < CACHE_DURATION_MINUTES * 60
  ) {
    return entry.data as T;
  }
  return null;
}

function setCache<T>(key: string, data: T): void {
  cache.set(key, { data, timestamp: Date.now() });
}

export async function clearCache(): Promise<void> {
  cache.clear();
}

function normalizeKey(raw: any, saveToPath?: string): SimpleKeyInfo {
  return {
    required: raw.required ?? false,
    onlyForFormats: raw.only_for_formats?.map((rec: string) =>
      rec.toLowerCase(),
    ),
    xmlDependsOn: raw.xml_depends_on ?? undefined,
    saveToPath: saveToPath,
  };
}

export async function getDonorMappingSchema(): Promise<DonorMap> {
  const cached = getCached<DonorMap>("donorMappingSchema");
  if (cached) return cached;

  try {
    const response = await fetch(`${BASE_URL}/donor-mapping-schema`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(
        `Failed to fetch donor mapping schema: ${response.statusText}`,
      );
    }

    const data = await response.json();
    const mappedData: DonorMap = {
      id: normalizeKey(data.id),
      gender: normalizeKey(data.gender),
      birthDate: normalizeKey(data.birth_date),
    };

    setCache("donorMappingSchema", mappedData);
    return mappedData;
  } catch (error) {
    console.error("Error fetching donor mapping schema:", error);
    throw error;
  }
}

export async function getSampleMappingSchema(): Promise<SampleMap> {
  const cached = getCached<SampleMap>("sampleMappingSchema");
  if (cached) return cached;

  try {
    const response = await fetch(`${BASE_URL}/sample-mapping-schema`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(
        `Failed to fetch sample mapping schema: ${response.statusText}`,
      );
    }

    const data = await response.json();

    const mappedData: SampleMap = {
      id: normalizeKey(data.id, "sample_details"),
      material_type: normalizeKey(data.material_type, "sample_details"),
      diagnosis: normalizeKey(data.diagnosis, "sample_details"),
      diagnosis_date: normalizeKey(data.diagnosis_date, "sample_details"),
      collection_date: normalizeKey(data.collection_date, "sample_details"),
      storage_temperature: normalizeKey(
        data.storage_temperature,
        "sample_details",
      ),
      collection: normalizeKey(data.collection, "sample_details"),
      donor_id: normalizeKey(data.donor_id),
      sample: normalizeKey(data.sample),
    };

    setCache("sampleMappingSchema", mappedData);
    return mappedData;
  } catch (error) {
    console.error("Error fetching sample mapping schema:", error);
    throw error;
  }
}

export async function getConditionMappingSchema(): Promise<ConditionMap> {
  const cached = getCached<ConditionMap>("conditionMappingSchema");
  if (cached) return cached;

  try {
    const response = await fetch(`${BASE_URL}/condition-mapping-schema`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(
        `Failed to fetch condition mapping schema: ${response.statusText}`,
      );
    }

    const data = await response.json();
    const mapped: ConditionMap = {
      "icd-10_code": normalizeKey(data["icd-10_code"]),
      patient_id: normalizeKey(data.patient_id),
      diagnosis_date: normalizeKey(data.diagnosis_date),
    };

    setCache("conditionMappingSchema", mapped);
    return mapped;
  } catch (error) {
    console.error("Error fetching condition mapping schema:", error);
    throw error;
  }
}

export async function getTemperatureValues(): Promise<string[]> {
  const cached = getCached<string[]>("temperatureValues");
  if (cached) return cached;

  try {
    const response = await fetch(`${BASE_URL}/storage-temperatures`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(
        `Failed to fetch storage temperatures: ${response.statusText}`,
      );
    }

    const data = await response.json();
    const values: string[] = data.storage_temperature;

    setCache("temperatureValues", values);
    return values;
  } catch (error) {
    console.error("Error fetching storage temperatures:", error);
    throw error;
  }
}

export async function getConfigValue(key: string): Promise<string | null> {
  try {
    const response = await fetch(
      `${BASE_URL}/config-value?key=${encodeURIComponent(key)}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      },
    );

    if (!response.ok) {
      throw new Error(
        `Failed to fetch config value for key ${key}: ${response.statusText}`,
      );
    }

    const data = await response.json();
    return data.value || null;
  } catch (error) {
    console.error(`Error fetching config value for key ${key}:`, error);
    return null;
  }
}

export async function getSampleCollectionIdentifiers(): Promise<string[]> {
  try {
    const fs = await import("node:fs");

    const filePath = await getConfigValue("SAMPLE_COLLECTIONS_PATH");
    if (!filePath) {
      return [];
    }

    if (!fs.existsSync(filePath)) {
      return [];
    }

    const fileContent = fs.readFileSync(filePath, "utf-8");
    const collections = JSON.parse(fileContent);

    if (!Array.isArray(collections)) {
      return [];
    }

    return collections
      .filter(
        (c): c is { identifier: string } =>
          typeof c === "object" &&
          c !== null &&
          typeof c.identifier === "string",
      )
      .map((c) => c.identifier);
  } catch (error) {
    console.error("Error fetching sample collection identifiers:", error);
    return [];
  }
}

function parseFileByExtension(
  content: string,
  fileExtension: string,
  csvSeparator?: string,
): DataField[] {
  if (fileExtension === ".json") return parseJsonFile(content);
  if (fileExtension === ".csv") return parseCsvFile(content, csvSeparator);
  if (fileExtension === ".xml") return parseXmlFile(content);
  return [];
}

function mergeFieldIntoMap(
  pathsMap: Map<string, DataField>,
  field: DataField,
): void {
  const existing = pathsMap.get(field.path);
  if (!existing) {
    pathsMap.set(field.path, field);
    return;
  }
  const hasMoreAttributes =
    field.attributes &&
    (!existing.attributes ||
      field.attributes.length > existing.attributes.length);
  if (hasMoreAttributes) {
    pathsMap.set(field.path, field);
  }
}

function collectFieldsFromFiles(
  files: { name: string; content: string }[],
  fileExtension: string,
  csvSeparator?: string,
): Map<string, DataField> {
  const pathsMap = new Map<string, DataField>();

  for (const file of files) {
    try {
      const fileFields = parseFileByExtension(
        file.content,
        fileExtension,
        csvSeparator,
      );
      for (const field of fileFields) {
        mergeFieldIntoMap(pathsMap, field);
      }
    } catch (parseError) {
      const msg =
        parseError instanceof Error ? parseError.message : "Unknown error";
      console.warn(`Failed to parse ${file.name}: ${msg}`);
    }
  }

  return pathsMap;
}

export async function parseDataFromFolder(
  folderPath: string,
  csvSeparator?: string,
): Promise<ParsedDataResult> {
  try {
    const data = await parseMultipleFolderData(folderPath);

    if (!data.success) {
      return { success: false, message: data.message };
    }

    const filesCount = data.files.length;
    const pathsMap = collectFieldsFromFiles(
      data.files,
      data.fileExtension!,
      csvSeparator,
    );

    if (pathsMap.size === 0) {
      return {
        success: false,
        message: `No fields could be parsed from the ${filesCount} file(s) found`,
      };
    }

    const fields = Array.from(pathsMap.values());
    return {
      success: true,
      message: `Successfully parsed ${fields.length} unique fields from ${filesCount} file(s)`,
      fields,
    };
  } catch (error) {
    const msg =
      error instanceof Error ? error.message : "Failed to parse folder data";
    console.error("Error parsing folder data:", error);
    return { success: false, message: msg };
  }
}

function parseJsonFile(fileContent: string): DataField[] {
  const data = JSON.parse(fileContent);

  // If the JSON contains an array of records, use only the first record for field mapping
  // The values from the first record will be common for mapping all subrecords
  let dataToAnalyze = data;
  if (Array.isArray(data) && data.length > 0) {
    dataToAnalyze = data[0];
  }

  const keys = getJSONKeys(dataToAnalyze);

  return keys;
}

function getJSONKeys(
  obj: any,
  path: string = "",
  xmlMode: boolean = false,
): DataField[] {
  const result: DataField[] = [];

  for (const key in obj) {
    const currentPath = path ? `${path}.${key}` : key;

    if (Array.isArray(obj[key]) && obj[key].length > 0) {
      const firstElement = obj[key][0];
      const attributes = Object.keys(firstElement).filter((attr) =>
        attr.startsWith("@"),
      );
      const nonAttributeEntries = Object.fromEntries(
        Object.entries(firstElement).filter(([attr]) => !attr.startsWith("@")),
      );

      result.push(...getJSONKeys(nonAttributeEntries, currentPath, xmlMode), {
        name: key,
        path: currentPath,
        attributes,
        example: "array",
      });
      continue;
    }

    if (obj[key] instanceof Object && !Array.isArray(obj[key])) {
      const attributes = Object.keys(obj[key]).filter((attr) =>
        attr.startsWith("@"),
      );
      const nonAttributeEntries = Object.fromEntries(
        Object.entries(obj[key]).filter(([attr]) => !attr.startsWith("@")),
      );

      result.push(...getJSONKeys(nonAttributeEntries, currentPath, xmlMode), {
        name: key,
        path: currentPath,
        attributes,
        example: "object",
      });
      continue;
    }

    result.push({ name: key, path: currentPath, example: obj[key] });
  }

  return result;
}

function parseCsvFile(
  fileContent: string,
  separator: string = ",",
): DataField[] {
  const lines = fileContent.split("\n").filter((line: string) => line.trim());

  if (lines.length < 2) {
    return [];
  }

  const headers = lines[0]
    .split(separator)
    .map((h: string) => h.trim().replaceAll(/['"]/g, ""));

  const values =
    lines[1]
      ?.split(separator)
      ?.map((h: string) => h.trim().replaceAll(/['"]/g, "")) || [];

  const fields: DataField[] = [];
  for (let i = 0; i < headers.length; i++) {
    const header = headers[i];
    fields.push({
      name: header,
      path: header,
      example: values[i],
    });
  }

  return fields;
}

function parseXmlFile(fileContent: string): DataField[] {
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
  const jsonData = parser.parse(fileContent);

  const filteredData = filterXmlMetadata(jsonData);

  return getJSONKeys(filteredData);
}

function filterXmlMetadata(jsonData: any): any {
  if (!jsonData || typeof jsonData !== "object") {
    return jsonData;
  }

  const filtered = { ...jsonData };

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
