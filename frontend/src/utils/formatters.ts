import type { MomentumStats, MoverDirection, MoverRecord, WatchlistScore } from "../types/mover";

export const watchlist = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"];

export function formatDate(value: string): string {
  const date = new Date(`${value}T00:00:00Z`);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
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

export function getMoverDirection(record: MoverRecord): MoverDirection {
  return record.direction === "down" || record.percent_change < 0 ? "down" : "up";
}

export function getTickerClass(record: MoverRecord | WatchlistScore): string {
  const direction = "percent_change" in record ? getMoverDirection(record) : record.direction;
  return direction === "down" ? "negative" : "positive";
}

export function getBarWidth(value: number, maxValue: number): string {
  const width = maxValue > 0 ? (Math.abs(value) / maxValue) * 100 : 0;
  return `${Math.max(width, value === 0 ? 0 : 8)}%`;
}

function getWatchlistLeaderboard(records: MoverRecord[]): WatchlistScore[] {
  const scores = watchlist.map((ticker) => {
    const tickerRecords = records.filter((record) => record.ticker === ticker);
    const latestTickerRecord = tickerRecords[0] ?? null;
    const bestMove = tickerRecords.reduce(
      (best, record) => Math.max(best, Math.abs(record.percent_change)),
      0,
    );

    return {
      ticker,
      wins: tickerRecords.length,
      bestMove,
      latestMove: latestTickerRecord?.percent_change ?? null,
      latestDate: latestTickerRecord?.date ?? null,
      latestClose: latestTickerRecord?.close_price ?? null,
      direction: latestTickerRecord ? getMoverDirection(latestTickerRecord) : null,
    };
  });

  return scores.sort((first, second) => {
    if (second.wins !== first.wins) {
      return second.wins - first.wins;
    }

    if (second.bestMove !== first.bestMove) {
      return second.bestMove - first.bestMove;
    }

    return watchlist.indexOf(first.ticker) - watchlist.indexOf(second.ticker);
  });
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

  const gainDays = records.filter((record) => getMoverDirection(record) === "up").length;
  const lossDays = records.filter((record) => getMoverDirection(record) === "down").length;
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

  const currentStreakTicker: string | null = latestMover?.ticker ?? null;
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
    leaderboard: getWatchlistLeaderboard(records),
  };
}
