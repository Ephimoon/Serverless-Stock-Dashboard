import type { MoverDirection, MoversApiResponse, MoverRecord } from "../types/mover";

const fallbackApiBaseUrl = "https://o3k1sp6nhf.execute-api.us-east-1.amazonaws.com/prod";

function getApiBaseUrl(): string {
  const configuredUrl = import.meta.env.VITE_API_BASE_URL;
  return (configuredUrl || fallbackApiBaseUrl).replace(/\/$/, "");
}

function toFiniteNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
}

function normalizeDirection(value: unknown, percentChange: number): MoverDirection {
  if (value === "up" || value === "down") {
    return value;
  }

  return percentChange >= 0 ? "up" : "down";
}

function normalizeMoverRecord(value: unknown): MoverRecord | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const record = value as Record<string, unknown>;
  const percentChange = toFiniteNumber(record.percent_change);
  const closePrice = toFiniteNumber(record.close_price);

  if (typeof record.date !== "string" || typeof record.ticker !== "string") {
    return null;
  }

  if (percentChange === null || closePrice === null) {
    return null;
  }

  return {
    date: record.date,
    ticker: record.ticker,
    percent_change: percentChange,
    close_price: closePrice,
    direction: normalizeDirection(record.direction, percentChange),
  };
}

function normalizeMoversApiResponse(value: unknown): MoversApiResponse | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const response = value as Record<string, unknown>;
  const normalizedItems = Array.isArray(response.items)
    ? response.items.map(normalizeMoverRecord)
    : null;

  if (!normalizedItems || normalizedItems.some((item) => item === null)) {
    return null;
  }

  const items = normalizedItems.filter((item): item is MoverRecord => item !== null);
  const count = toFiniteNumber(response.count) ?? items.length;
  const limit = toFiniteNumber(response.limit) ?? items.length;

  return {
    items,
    count,
    limit,
    next_cursor: typeof response.next_cursor === "string" || response.next_cursor === null
      ? response.next_cursor
      : null,
    has_more: response.has_more === true,
  };
}

async function getErrorMessage(response: Response): Promise<string> {
  try {
    const data: unknown = await response.json();

    if (data && typeof data === "object" && typeof (data as { message?: unknown }).message === "string") {
      return (data as { message: string }).message;
    }
  } catch {
    // The status code is still useful when the response body is not JSON.
  }

  return `status ${response.status}`;
}

export async function fetchMovers(limit = 7, cursor: string | null = null): Promise<MoversApiResponse> {
  const params = new URLSearchParams({ limit: String(limit) });

  if (cursor) {
    params.set("cursor", cursor);
  }

  const url = `${getApiBaseUrl()}/movers?${params.toString()}`;
  const response = await fetch(url);

  if (!response.ok) {
    const detail = await getErrorMessage(response);
    throw new Error(`The movers API returned ${detail}.`);
  }

  const data: unknown = await response.json();
  const normalized = normalizeMoversApiResponse(data);

  if (!normalized) {
    throw new Error("The movers API returned an unexpected response shape.");
  }

  return normalized;
}
