"use server";

export interface ConfigurationInfo {
  miabisOnFhir: boolean;
}

/**
 * Get configuration info from environment variables.
 * This replaces the Python /configuration-info endpoint since
 * the Python code and UI share the same Docker container.
 */
export async function getConfigurationInfo(): Promise<ConfigurationInfo> {
  const miabisOnFhir =
    process.env.MIABIS_ON_FHIR?.toLowerCase() === "true" || false;

  return {
    miabisOnFhir,
  };
}
