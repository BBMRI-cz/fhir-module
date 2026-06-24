import "server-only";

import { ProxyAgent, fetch as undiciFetch } from "undici";
import type { RequestInit } from "undici";

let proxyAgent: ProxyAgent | undefined;
let proxyAgentUrl: string | undefined;

function validateOutboundUrl(rawUrl: string): string {
  const parsed = new URL(rawUrl);

  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error(`Unsupported URL protocol: ${parsed.protocol}`);
  }

  return parsed.toString();
}

export async function proxyFetch(
  url: string,
  init?: RequestInit
): Promise<Response> {
  const safeUrl = validateOutboundUrl(url);

  const proxyUrl =
    (safeUrl.startsWith("https:")
      ? process.env.HTTPS_PROXY ?? process.env.https_proxy
      : process.env.HTTP_PROXY ?? process.env.http_proxy) ??
    process.env.ALL_PROXY ??
    process.env.all_proxy;

  if (!proxyUrl) {
    return fetch(safeUrl, init as globalThis.RequestInit);
  }

  if (!proxyAgent || proxyAgentUrl !== proxyUrl) {
    proxyAgentUrl = proxyUrl;
    proxyAgent = new ProxyAgent(proxyUrl);
  }

  return (await undiciFetch(safeUrl, {
    ...init,
    dispatcher: proxyAgent,
  })) as unknown as Response;
}