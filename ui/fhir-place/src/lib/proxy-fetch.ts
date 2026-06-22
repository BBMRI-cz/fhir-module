"server-only";

import { ProxyAgent, fetch as undiciFetch } from "undici";
import type { RequestInit } from "undici";

export async function proxyFetch(
  url: string,
  init?: RequestInit
): Promise<Response> {
  const proxyUrl = process.env.HTTPS_PROXY ?? process.env.HTTP_PROXY;

  if (!proxyUrl) {
    return fetch(url, init as globalThis.RequestInit);
  }

  return undiciFetch(url, {
    ...init,
    dispatcher: new ProxyAgent(proxyUrl),
  }) as unknown as Response;
}