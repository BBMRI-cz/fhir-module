"use server";

const BASE_URL = process.env.BACKEND_API_URL || "http://localhost:5000";

export interface ParsedMappings {
  parsing_map: {
    donor_map?: Record<string, string>;
    sample_map?: Record<string, unknown>;
    condition_map?: Record<string, string>;
  };
  blaze_material_mapping: Record<string, string>;
  blaze_temperature_mapping: Record<string, string>;
  type_to_collection_mapping: Record<string, string>;
  miabis_on_fhir: boolean;
  miabis_material_mapping?: Record<string, string>;
  miabis_temperature_mapping?: Record<string, string>;
}

export async function getMappings(): Promise<ParsedMappings | null> {
  try {
    const response = await fetch(`${BASE_URL}/mappings`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    });

    if (!response.ok) {
      console.error(`Failed to fetch mappings: ${response.statusText}`);
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching mappings:", error);
    return null;
  }
}