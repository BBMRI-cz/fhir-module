"server-only";

import { ProxyAgent, fetch as undiciFetch } from "undici";
import type { RequestInit } from "undici";

function validateOutboundUrl(rawUrl: string): string {
  const parsed = new URL(rawUrl);

  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error(`Unsupported URL protocol: ${parsed.protocol}`);
  }

  if (parsed.username || parsed.password) {
    throw new Error("Outbound URL must not contain credentials");
  }

  return parsed.toString();
}

export async function proxyFetch(
  url: string,
  init?: RequestInit
): Promise<Response> {
  const safeUrl = validateOutboundUrl(url);
  const proxyUrl = process.env.HTTPS_PROXY ?? process.env.HTTP_PROXY;

  if (!proxyUrl) {
    return fetch(safeUrl, init as globalThis.RequestInit);
  }

  return undiciFetch(safeUrl, {
    ...init,
    dispatcher: new ProxyAgent(proxyUrl),
  }) as unknown as Response;
}