import type { MoversApiResponse, MoverRecord } from "../types/mover";

const fallbackApiBaseUrl = "https://o3k1sp6nhf.execute-api.us-east-1.amazonaws.com/prod";

function getApiBaseUrl(): string {
  const configuredUrl = import.meta.env.VITE_API_BASE_URL;
  return (configuredUrl || fallbackApiBaseUrl).replace(/\/$/, "");
}

function isMoverRecord(value: unknown): value is MoverRecord {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return typeof record.date === "string"
    && typeof record.ticker === "string"
    && typeof record.percent_change === "number"
    && typeof record.close_price === "number"
    && (record.direction === "up" || record.direction === "down");
}

function isMoversApiResponse(value: unknown): value is MoversApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const response = value as Record<string, unknown>;

  return Array.isArray(response.items)
    && response.items.every(isMoverRecord)
    && typeof response.count === "number"
    && typeof response.limit === "number"
    && (typeof response.next_cursor === "string" || response.next_cursor === null)
    && typeof response.has_more === "boolean";
}

export async function fetchMovers(limit = 7, signal?: AbortSignal): Promise<MoversApiResponse> {
  const url = `${getApiBaseUrl()}/movers?limit=${limit}`;
  const response = await fetch(url, { signal });

  if (!response.ok) {
    throw new Error(`The movers API returned ${response.status}.`);
  }

  const data: unknown = await response.json();

  if (!isMoversApiResponse(data)) {
    throw new Error("The movers API returned an unexpected response shape.");
  }

  return data;
}
