export type MoverDirection = "up" | "down";

export interface MoverRecord {
  date: string;
  ticker: string;
  percent_change: number;
  close_price: number;
  direction: MoverDirection;
}

export interface MoversApiResponse {
  items: MoverRecord[];
  count: number;
  limit: number;
  next_cursor: string | null;
  has_more: boolean;
}

export interface WatchlistScore {
  ticker: string;
  wins: number;
  bestMove: number;
  latestMove: number | null;
  latestDate: string | null;
  latestClose: number | null;
  direction: MoverDirection | null;
}

export interface MomentumStats {
  latestMover: MoverRecord | null;
  biggestMover: MoverRecord | null;
  averageAbsoluteMove: number;
  gainDays: number;
  lossDays: number;
  mostFrequentTicker: string | null;
  mostFrequentWins: number;
  currentStreakTicker: string | null;
  currentStreakCount: number;
  marketMood: "Bullish" | "Bearish" | "Mixed" | "No data";
  leaderboard: WatchlistScore[];
}
