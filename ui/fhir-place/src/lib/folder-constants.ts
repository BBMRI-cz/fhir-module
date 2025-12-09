/** Maximum number of files to display in folder explorer UI */
export const MAX_FILES_LIMIT = 10;

/** Maximum entries to scan when listing directories (prevents freeze on huge folders) */
export const MAX_ENTRIES_TO_SCAN = 1000;

/** Maximum files to scan when parsing folder for field extraction */
export const MAX_FILES_TO_SCAN = 1000;

/** Maximum files to process when extracting values from paths */
export const MAX_FILES_TO_PROCESS = 1000;

/** Supported data file extensions */
export const SUPPORTED_EXTENSIONS: string[] = [".json", ".csv", ".xml"];
