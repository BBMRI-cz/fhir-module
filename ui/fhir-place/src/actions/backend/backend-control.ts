"use server";

export interface BackendActionResult {
  success: boolean;
  message: string;
  data?: unknown;
}

async function callBackendAPI(
  endpoint: string,
  method: string = "POST"
): Promise<BackendActionResult> {
  const BACKEND_BASE_URL =
    process.env.BACKEND_API_URL || "http://localhost:5000";

  try {
    const response = await fetch(`${BACKEND_BASE_URL}${endpoint}`, {
      method,
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      return {
        success: false,
        message: `Backend API request failed: ${response.status} ${response.statusText}`,
      };
    }

    const data = await response.json();

    return {
      success: true,
      message: data.message || "Operation completed successfully",
      data,
    };
  } catch (error) {
    console.error("Error calling backend API:", error);

    return {
      success: false,
      message:
        error instanceof Error
          ? error.message
          : "An unexpected error occurred while calling the backend API",
    };
  }
}

export async function syncAction(): Promise<BackendActionResult> {
  return await callBackendAPI("/sync", "POST");
}

export async function miabisSyncAction(): Promise<BackendActionResult> {
  return await callBackendAPI("/miabis-sync", "POST");
}

export async function deleteAllAction(): Promise<BackendActionResult> {
  return await callBackendAPI("/delete", "POST");
}

export async function miabisDeleteAction(): Promise<BackendActionResult> {
  return await callBackendAPI("/miabis-delete", "POST");
}
