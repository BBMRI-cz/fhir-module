"use server";

const BACKEND_BASE_URL = process.env.BACKEND_API_URL || "http://localhost:5000";

export interface SetupStatus {
  initialSetupComplete: boolean;
}

export async function getSetupStatus(): Promise<SetupStatus> {
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/setup-status`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      return {
        initialSetupComplete: false,
      };
    }

    const data = await response.json();
    return {
      initialSetupComplete: data.initial_setup_complete ?? false,
    };
  } catch (error) {
    console.error("Error fetching setup status:", error);
    return {
      initialSetupComplete: false,
    };
  }
}

export async function markSetupComplete(): Promise<{ success: boolean }> {
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/setup-status`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        initial_setup_complete: true,
      }),
    });

    if (!response.ok) {
      return { success: false };
    }

    return { success: true };
  } catch (error) {
    console.error("Error marking setup complete:", error);
    return { success: false };
  }
}
