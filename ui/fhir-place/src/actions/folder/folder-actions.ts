"use server";

import { FolderTreeRecord } from "@/types/actions/folder/types";

// FHIR Module API base URL - uses the same backend API URL as other services
const FHIR_MODULE_API_BASE =
  process.env.BACKEND_API_URL || "http://localhost:5001";

export async function getFolders(
  folderPath: string = "",
  includeFiles: boolean = false
): Promise<FolderTreeRecord[]> {
  try {
    const targetPath = folderPath || "/";

    const url = new URL("/list-directories", FHIR_MODULE_API_BASE);
    url.searchParams.set("path", targetPath);
    url.searchParams.set("include_files", includeFiles.toString());

    const response = await fetch(url.toString(), {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage =
        errorData.error || `HTTP ${response.status}: ${response.statusText}`;
      throw new Error(`Failed to fetch folders: ${errorMessage}`);
    }

    const data = await response.json();

    if (!data.entries || !Array.isArray(data.entries)) {
      throw new Error("Invalid response format from FHIR module API");
    }

    const result: FolderTreeRecord[] = data.entries.map(
      (entry: { name: string; path: string; isDirectory: boolean }) => ({
        name: entry.name,
        path: entry.path,
        isDirectory: entry.isDirectory,
      })
    );

    return result;
  } catch (err) {
    console.error("Error fetching folders from FHIR module:", err);
    throw new Error(`Failed to fetch folders: ${(err as Error).message}`);
  }
}
