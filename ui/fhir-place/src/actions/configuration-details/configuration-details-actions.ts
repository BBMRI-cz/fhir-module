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

const BASE_URL = process.env.BACKEND_API_URL || "http://localhost:5001";

function normalizeKey(raw: any, saveToPath?: string): SimpleKeyInfo {
  return {
    required: raw.required ?? false,
    onlyForFormats: raw.only_for_formats?.map((rec: string) =>
      rec.toLowerCase()
    ),
    xmlDependsOn: raw.xml_depends_on ?? undefined,
    saveToPath: saveToPath,
  };
}

export async function getDonorMappingSchema(): Promise<DonorMap> {
  try {
    const response = await fetch(`${BASE_URL}/donor-mapping-schema`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(
        `Failed to fetch donor mapping schema: ${response.statusText}`
      );
    }

    const data = await response.json();
    const mappedData: DonorMap = {
      id: normalizeKey(data.id),
      gender: normalizeKey(data.gender),
      birthDate: normalizeKey(data.birth_date),
    };

    return mappedData;
  } catch (error) {
    console.error("Error fetching donor mapping schema:", error);
    throw error;
  }
}

export async function getSampleMappingSchema(): Promise<SampleMap> {
  try {
    const response = await fetch(`${BASE_URL}/sample-mapping-schema`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(
        `Failed to fetch sample mapping schema: ${response.statusText}`
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
        "sample_details"
      ),
      collection: normalizeKey(data.collection, "sample_details"),
      donor_id: normalizeKey(data.donor_id),
      sample: normalizeKey(data.sample),
    };

    return mappedData;
  } catch (error) {
    console.error("Error fetching sample mapping schema:", error);
    throw error;
  }
}

export async function getConditionMappingSchema(): Promise<ConditionMap> {
  try {
    const response = await fetch(`${BASE_URL}/condition-mapping-schema`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(
        `Failed to fetch condition mapping schema: ${response.statusText}`
      );
    }

    const data = await response.json();
    const mapped: ConditionMap = {
      "icd-10_code": normalizeKey(data["icd-10_code"]),
      patient_id: normalizeKey(data.patient_id),
      diagnosis_date: normalizeKey(data.diagnosis_date),
    };

    return mapped;
  } catch (error) {
    console.error("Error fetching condition mapping schema:", error);
    throw error;
  }
}

export async function getTemperatureValues(): Promise<string[]> {
  try {
    const response = await fetch(`${BASE_URL}/storage-temperatures`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(
        `Failed to fetch storage temperatures: ${response.statusText}`
      );
    }

    const data = await response.json();
    return data.storage_temperature;
  } catch (error) {
    console.error("Error fetching storage temperatures:", error);
    throw error;
  }
}

// Cache for material types
let _materialTypesCache: string[] | null = null;
let _cacheTimestamp: Date | null = null;
const CACHE_DURATION_MINUTES = 60;

// Taken from the python lib, there is no docs it could be fetched from
const MIABIS_MATERIAL_TYPES = [
  "AmnioticFluid",
  "AscitesFluid",
  "Bile",
  "BodyCavityFluid",
  "Bone",
  "BoneMarrowAspirate",
  "BoneMarrowPlasma",
  "BoneMarrowWhole",
  "BreastMilk",
  "BronchLavage",
  "BuffyCoat",
  "CancerCellLine",
  "CerebrospinalFluid",
  "CordBlood",
  "DentalPulp",
  "DNA",
  "Embryo",
  "EntireOrgan",
  "Faeces",
  "FetalTissue",
  "Fibroblast",
  "FoodSpecimen",
  "Gas",
  "GastricFluid",
  "Hair",
  "ImmortalizedCellLine",
  "IsolatedMicrobe",
  "IsolatedExosome",
  "IsolatedTumorCell",
  "LiquidBiopsy",
  "MenstrualBlood",
  "Nail",
  "NasalWashing",
  "Organoid",
  "Other",
  "PericardialFluid",
  "PBMC",
  "Placenta",
  "Plasma",
  "PleuralFluid",
  "PostMortemTissue",
  "PrimaryCells",
  "Protein",
  "RedBloodCells",
  "RNA",
  "Saliva",
  "Semen",
  "Serum",
  "SpecimenEnvironment",
  "Sputum",
  "StemCells",
  "Swab",
  "Sweat",
  "SynovialFluid",
  "Tears",
  "Teeth",
  "TissueFixed",
  "TissueFreshFrozen",
  "UmbilicalCord",
  "Urine",
  "UrineSediment",
  "VitreousFluid",
  "WholeBlood",
  "WholeBloodDried",
];
/**
 * Recursively extract concept codes from FHIR ValueSet response
 */
function extractConceptsFromFetch(data: any): string[] {
  const concepts: string[] = [];

  if (typeof data === "object" && data !== null && !Array.isArray(data)) {
    // Check if this object has a code
    const code = data.code;
    if (code) {
      concepts.push(code);
    }

    // Recursively process concept property
    const concept = data.concept;
    if (concept) {
      concepts.push(...extractConceptsFromFetch(concept));
    }
  }

  if (Array.isArray(data)) {
    for (const item of data) {
      concepts.push(...extractConceptsFromFetch(item));
    }
  }

  return concepts;
}

/**
 * Fetch material types from BBMRI.de Simplifier API with caching.
 * Returns a list of material type codes.
 */
export async function getMaterialTypes(isMiabis: boolean): Promise<string[]> {
  if (isMiabis) {
    return MIABIS_MATERIAL_TYPES;
  }

  if (
    _materialTypesCache !== null &&
    _cacheTimestamp !== null &&
    (Date.now() - _cacheTimestamp.getTime()) / 1000 <
      CACHE_DURATION_MINUTES * 60
  ) {
    return _materialTypesCache;
  }

  try {
    const url =
      "https://simplifier.net/bbmri.de/samplematerialtype/$download?format=json";
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch material types: ${response.statusText}`);
    }

    const data = await response.json();
    const materialTypes = extractConceptsFromFetch(data);

    // Update cache
    _materialTypesCache = materialTypes;
    _cacheTimestamp = new Date();

    return materialTypes;
  } catch (error) {
    console.error("Error fetching material types from BBMRI.de API:", error);
    throw error;
  }
}

export async function parseDataFromFolder(
  folderPath: string,
  csvSeparator?: string
): Promise<ParsedDataResult> {
  try {
    const BACKEND_BASE_URL =
      process.env.BACKEND_API_URL || "http://localhost:5000";

    const response = await fetch(`${BACKEND_BASE_URL}/parse-folder-data`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        folderPath: folderPath,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return {
        success: false,
        message:
          errorData.message ||
          `Backend API request failed: ${response.status} ${response.statusText}`,
      };
    }

    const data = await response.json();

    if (!data.success) {
      return {
        success: false,
        message: data.message,
      };
    }

    // Parse the file content using the appropriate parser
    let fields: DataField[] = [];
    const fileContent = data.fileContent;
    const fileExtension = data.fileExtension;
    const fileName = data.fileName;

    try {
      if (fileExtension === ".json") {
        fields = parseJsonFile(fileContent);
      } else if (fileExtension === ".csv") {
        fields = parseCsvFile(fileContent, csvSeparator);
      } else if (fileExtension === ".xml") {
        fields = parseXmlFile(fileContent);
      } else {
        return {
          success: false,
          message: `Unsupported file type: ${fileExtension}`,
        };
      }
    } catch (parseError) {
      return {
        success: false,
        message: `Error parsing ${fileName}: ${
          parseError instanceof Error
            ? parseError.message
            : "Unknown parsing error"
        }`,
      };
    }

    return {
      success: true,
      message: `Successfully parsed ${fields.length} fields from ${fileName} (first file found)`,
      fields,
    };
  } catch (error) {
    console.error("Error parsing folder data:", error);
    return {
      success: false,
      message:
        error instanceof Error ? error.message : "Failed to parse folder data",
    };
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
  xmlMode: boolean = false
): DataField[] {
  const result: DataField[] = [];

  for (const key in obj) {
    const currentPath = path ? `${path}.${key}` : key;

    if (Array.isArray(obj[key]) && obj[key].length > 0) {
      const firstElement = obj[key][0];
      const attributes = Object.keys(firstElement).filter((attr) =>
        attr.startsWith("@")
      );
      const nonAttributeEntries = Object.fromEntries(
        Object.entries(firstElement).filter(([attr]) => !attr.startsWith("@"))
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
        attr.startsWith("@")
      );
      const nonAttributeEntries = Object.fromEntries(
        Object.entries(obj[key]).filter(([attr]) => !attr.startsWith("@"))
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
  separator: string = ","
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
