"use server";

const BACKEND_BASE_URL = process.env.BACKEND_API_URL || "http://localhost:5000";

export interface ModeResult {
  isMiabisMode: boolean;
}

export async function getMode(): Promise<ModeResult> {
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/configuration-info`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      console.error("Failed to fetch configuration info from backend");
      return { isMiabisMode: false };
    }

    const data = await response.json();
    return {
      isMiabisMode: data.miabis_on_fhir ?? false,
    };
  } catch (error) {
    console.error("Error fetching configuration info:", error);
    return { isMiabisMode: false };
  }
}

