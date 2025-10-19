"use server";

import { SyncTarget } from "@/types/setup-wizard/types";

export async function getViableSyncTargets(): Promise<SyncTarget[]> {
  const result: SyncTarget[] = [];

  const blazeSyncTarget = process.env.BLAZE_URL;

  if (blazeSyncTarget) {
    result.push("blaze" as SyncTarget);
  }

  const miabisSyncTarget = process.env.MIABIS_BLAZE_URL;
  const miabisOnFhir = process.env.MIABIS_ON_FHIR?.toLowerCase() === "true";

  if (miabisSyncTarget && miabisOnFhir) {
    result.push("miabis" as SyncTarget);
  }

  if (blazeSyncTarget && miabisSyncTarget && miabisOnFhir) {
    result.push("both" as SyncTarget);
  }

  return result;
}
