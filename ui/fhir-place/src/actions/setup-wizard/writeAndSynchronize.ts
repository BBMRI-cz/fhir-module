"use server";
import { prepareBody } from "@/actions/setup-wizard/mappingChangeHelper";
import { WizardState } from "@/types/setup-wizard/types";

const BACKEND_BASE_URL = process.env.BACKEND_API_URL || "http://localhost:5000";

export default async function writeAndSynchronize(
  wizardState: WizardState,
  fileType: string,
  recordsPath: string,
  csvSeparator?: string
) {
  try {
    const body = prepareBody({
      fileType,
      recordsPath,
      mappings: wizardState,
      csvSeparator,
      syncTarget: wizardState.syncTarget,
    });

    const response = await fetch(`${BACKEND_BASE_URL}/change-mappings`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      return { success: false };
    }

    return { success: true };
  } catch (error) {
    return {
      success: false,
      errors: [
        `An unexpected error occurred during validation (${
          error instanceof Error ? error.message : "Unknown error"
        }). Please try again.`,
      ],
    };
  }
}
