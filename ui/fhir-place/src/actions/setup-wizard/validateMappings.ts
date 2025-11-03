"use server";
import { prepareBody } from "@/actions/setup-wizard/mappingChangeHelper";
import {
  ConfigChangeBodyRequest,
  SyncTarget,
  ValidationResult,
  WizardState,
} from "@/types/setup-wizard/types";

const BACKEND_BASE_URL = process.env.BACKEND_API_URL || "http://localhost:5000";

export async function validateMappings(
  mappings: WizardState,
  fileType: string,
  recordsPath: string,
  syncTarget: SyncTarget,
  csvSeparator?: string,
  validateAllFiles?: boolean
): Promise<ValidationResult> {
  try {
    const body = prepareBody({
      fileType,
      recordsPath,
      mappings,
      csvSeparator,
      validateAllFiles,
      syncTarget,
    } as ConfigChangeBodyRequest);

    const response = await fetch(`${BACKEND_BASE_URL}/validate-mappings`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json();
      const genericErrors: string[] = [];

      if (typeof errorData?.message === "string") {
        genericErrors.push(errorData.message);
      }

      if (Array.isArray(errorData?.message?.generic_errors)) {
        genericErrors.push(...errorData.message.generic_errors);
      }

      return {
        success: false,
        genericErrors: genericErrors,
        patientErrors: errorData?.message.patient_errors,
        sampleErrors: errorData?.message.sample_errors,
        conditionErrors: errorData?.message.condition_errors,
      };
    }

    return { success: true };
  } catch (error) {
    return {
      success: false,
      genericErrors: [
        `An unexpected error occurred during validation (${
          error instanceof Error ? error.message : "Unknown error"
        }). Please try again.`,
      ],
    };
  }
}
