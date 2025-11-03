"use server";

import {
  parseXMLTotal,
  type ResourceCount,
} from "@/lib/fhir/resource-count-utils";

export interface ResourceCountsResponse {
  success: boolean;
  resources?: ResourceCount[];
  error?: string;
}

export async function getResourceCounts(): Promise<ResourceCountsResponse> {
  try {
    const blazeUrl = process.env.BLAZE_URL || "http://localhost:8080/fhir";

    const resourceTypes = ["Organization", "Patient", "Condition", "Specimen"];

    const counts = await Promise.all(
      resourceTypes.map(async (resourceType) => ({
        resourceType,
        count: await fetchResourceCount(blazeUrl, resourceType),
      }))
    );

    return {
      success: true,
      resources: counts,
    };
  } catch (error) {
    console.error("Error fetching resource counts:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
}

export async function getMiabisResourceCounts(): Promise<ResourceCountsResponse> {
  try {
    const miaBlazeUrl =
      process.env.MIABIS_BLAZE_URL || "http://localhost:5432/fhir";

    const resourceMapping = [
      { displayType: "BiobankOrganization", fhirType: "Organization" },
      { displayType: "SampleCollection", fhirType: "Group" },
      { displayType: "Patient", fhirType: "Patient" },
      { displayType: "Specimen", fhirType: "Specimen" },
    ];

    const counts = await Promise.all(
      resourceMapping.map(async ({ displayType, fhirType }) => ({
        resourceType: displayType,
        count: await fetchResourceCount(miaBlazeUrl, fhirType),
      }))
    );

    return {
      success: true,
      resources: counts,
    };
  } catch (error) {
    console.error("Error fetching MIABIS resource counts:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
}

export async function fetchResourceCount(
  blazeUrl: string,
  resourceType: string
): Promise<number> {
  try {
    const response = await fetch(`${blazeUrl}/${resourceType}?_summary=count`, {
      method: "GET",
      headers: {
        Accept: "application/fhir+xml",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      console.error(
        `Failed to fetch ${resourceType}: ${response.status} ${response.statusText}`
      );
      return 0;
    }

    const xmlText = await response.text();
    return parseXMLTotal(xmlText);
  } catch (error) {
    console.error(`Error fetching ${resourceType} count:`, error);
    return 0;
  }
}
