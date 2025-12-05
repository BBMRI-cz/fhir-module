"use server";

let _materialTypesCache: string[] | null = null;
let _cacheTimestamp: Date | null = null;
const CACHE_DURATION_MINUTES = 60;

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
function extractConceptsFromFetch(data: unknown): string[] {
  const concepts: string[] = [];

  if (typeof data === "object" && data !== null && !Array.isArray(data)) {
    const obj = data as Record<string, unknown>;
    // Check if this object has a code
    const code = obj.code;
    if (typeof code === "string") {
      concepts.push(code);
    }

    const concept = obj.concept;
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

    _materialTypesCache = materialTypes;
    _cacheTimestamp = new Date();

    return materialTypes;
  } catch (error) {
    console.error("Error fetching material types from BBMRI.de API:", error);
    throw error;
  }
}
