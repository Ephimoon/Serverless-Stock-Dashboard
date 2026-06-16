import type { MomentumStats, MoverRecord } from "../types/mover";

export const watchlist = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"];

export function formatDate(value: string): string {
  const date = new Date(`${value}T00:00:00`);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

export function formatPercent(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function getTickerClass(record: MoverRecord): string {
  return record.direction === "up" ? "positive" : "negative";
}

export function getBarWidth(record: MoverRecord, records: MoverRecord[]): string {
  const maxMove = Math.max(...records.map((item) => Math.abs(item.percent_change)), 1);
  const width = Math.max((Math.abs(record.percent_change) / maxMove) * 100, 6);
  return `${width}%`;
}

export function calculateMomentum(records: MoverRecord[]): MomentumStats {
  const latestMover = records[0] ?? null;
  const biggestMover = records.reduce<MoverRecord | null>((currentBiggest, record) => {
    if (!currentBiggest) {
      return record;
    }

    return Math.abs(record.percent_change) > Math.abs(currentBiggest.percent_change)
      ? record
      : currentBiggest;
  }, null);

  const gainDays = records.filter((record) => record.direction === "up").length;
  const lossDays = records.filter((record) => record.direction === "down").length;
  const averageAbsoluteMove = records.length
    ? records.reduce((total, record) => total + Math.abs(record.percent_change), 0) / records.length
    : 0;

  const winsByTicker = records.reduce<Record<string, number>>((counts, record) => {
    counts[record.ticker] = (counts[record.ticker] ?? 0) + 1;
    return counts;
  }, {});

  const [mostFrequentTicker, mostFrequentWins] = Object.entries(winsByTicker).sort(
    (first, second) => second[1] - first[1],
  )[0] ?? [null, 0];

  let currentStreakTicker: string | null = latestMover?.ticker ?? null;
  let currentStreakCount = 0;

  if (currentStreakTicker) {
    for (const record of records) {
      if (record.ticker !== currentStreakTicker) {
        break;
      }

      currentStreakCount += 1;
    }
  }

  const marketMood = records.length === 0
    ? "No data"
    : gainDays > lossDays
      ? "Bullish"
      : lossDays > gainDays
        ? "Bearish"
        : "Mixed";

  return {
    latestMover,
    biggestMover,
    averageAbsoluteMove,
    gainDays,
    lossDays,
    mostFrequentTicker,
    mostFrequentWins,
    currentStreakTicker,
    currentStreakCount,
    marketMood,
  };
}
