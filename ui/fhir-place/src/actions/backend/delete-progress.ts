import { type ResourceCount } from "@/lib/fhir/resource-count-utils";
import { fetchResourceCount } from "@/actions/backend/get-resource-counts";

export interface DeleteProgressResponse {
  resources: ResourceCount[];
  success: boolean;
  error?: string;
}

export async function getDeleteProgress(
  mode: "blaze" | "miabis"
): Promise<DeleteProgressResponse> {
  try {
    const fhirUrl = resolveFhirUrl(mode);
    const resourceTypes =
      mode === "miabis"
        ? ["Group", "Patient", "Specimen"]
        : ["Patient", "Condition", "Specimen"];
    const resources: ResourceCount[] = [];

    for (const resourceType of resourceTypes) {
      const count = await fetchResourceCount(fhirUrl, resourceType);
      resources.push({
        resourceType,
        count,
      });
    }

    return {
      resources,
      success: true,
    };
  } catch (error) {
    console.error("Error fetching delete progress:", error);
    return {
      resources: [],
      success: false,
      error:
        error instanceof Error
          ? error.message
          : "An unexpected error occurred while fetching delete progress",
    };
  }
}

function resolveFhirUrl(mode: "blaze" | "miabis"): string {
  if (mode === "miabis") {
    return process.env.MIABIS_BLAZE_URL || "http://localhost:5432/fhir";
  } else {
    return process.env.BLAZE_URL || "http://localhost:8080/fhir";
  }
}
