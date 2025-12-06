"use server";

import { SyncTarget } from "@/types/setup-wizard/types";

async function isUrlReachable(url: string): Promise<boolean> {
  if (!url) return false;

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);

  try {
    const response = await fetch(url, {
      method: "GET",
      signal: controller.signal,
    });

    return response.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timeout);
  }
}

export async function getViableSyncTargets(): Promise<SyncTarget[]> {
  const result: SyncTarget[] = [];

  const blazeSyncTarget = process.env.BLAZE_URL ?? "";
  const miabisSyncTarget = process.env.MIABIS_BLAZE_URL ?? "";
  const miabisOnFhir =
    (process.env.MIABIS_ON_FHIR ?? "").toLowerCase() === "true";

  const [blazeUp, miabisUp] = await Promise.all([
    isUrlReachable(blazeSyncTarget),
    miabisOnFhir ? isUrlReachable(miabisSyncTarget) : Promise.resolve(false),
  ]);

  if (miabisUp) {
    result.push("miabis" as SyncTarget);
  }

  if (blazeUp) {
    result.push("blaze" as SyncTarget);
  }

  if (blazeUp && miabisUp) {
    result.push("both" as SyncTarget);
  }

  return result;
}
