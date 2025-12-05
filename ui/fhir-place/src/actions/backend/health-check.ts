"use server";

const BACKEND_BASE_URL = process.env.BACKEND_API_URL || "http://localhost:5000";

export interface HealthCheckResponse {
  isHealthy: boolean;
  error?: string;
}

export async function checkBackendHealth(): Promise<HealthCheckResponse> {
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/setup-status`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
    });

    if (!response.ok) {
      return {
        isHealthy: false,
        error: `Backend responded with status: ${response.status}`,
      };
    }

    return {
      isHealthy: true,
    };
  } catch (error) {
    console.error("Error checking backend health:", error);
    return {
      isHealthy: false,
      error:
        error instanceof Error ? error.message : "Failed to connect to backend",
    };
  }
}
