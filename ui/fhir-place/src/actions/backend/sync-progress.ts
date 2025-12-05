"use server";

export interface ResourceProgress {
  current: number;
  total?: number;
  percentage?: number;
}

export interface SyncProgressResponse {
  in_progress: boolean;
  current_phase: number;
  resources: Record<string, ResourceProgress>;
  error?: string;
}

async function fetchSyncProgressFromEndpoint(
  endpoint: string,
  syncType: string
): Promise<SyncProgressResponse> {
  const BACKEND_BASE_URL =
    process.env.BACKEND_API_URL || "http://localhost:5000";

  try {
    const response = await fetch(`${BACKEND_BASE_URL}${endpoint}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      return {
        in_progress: false,
        current_phase: 0,
        resources: {},
        error: `Failed to fetch ${syncType} sync progress: ${response.status}`,
      };
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`Error fetching ${syncType} sync progress:`, error);
    return {
      in_progress: false,
      current_phase: 0,
      resources: {},
      error:
        error instanceof Error
          ? error.message
          : `Failed to fetch ${syncType} sync progress`,
    };
  }
}

export async function getSyncProgress(): Promise<SyncProgressResponse> {
  return fetchSyncProgressFromEndpoint("/sync-progress", "standard");
}

export async function getMiabisSyncProgress(): Promise<SyncProgressResponse> {
  return fetchSyncProgressFromEndpoint("/miabis-sync-progress", "MIABIS");
}
