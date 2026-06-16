import type { MomentumStats } from "../types/mover";
import { formatCurrency, formatNumber, formatPercent } from "../utils/formatters";

interface SummaryCardsProps {
  stats: MomentumStats;
  recordCount: number;
}

export function SummaryCards({ stats, recordCount }: SummaryCardsProps) {
  const latestClass = stats.latestMover
    ? (stats.latestMover.direction === "down" || stats.latestMover.percent_change < 0 ? "negative" : "positive")
    : undefined;
  const latestTicker = stats.latestMover?.ticker ?? "No data";
  const latestMove = stats.latestMover ? formatPercent(stats.latestMover.percent_change) : "0.00%";
  const latestClose = stats.latestMover ? formatCurrency(stats.latestMover.close_price) : "Waiting for first run";
  const biggestTicker = stats.biggestMover?.ticker ?? "No data";
  const biggestMove = stats.biggestMover ? formatPercent(stats.biggestMover.percent_change) : "0.00%";
  const frequentTicker = stats.mostFrequentTicker ?? "No ticker";
  const frequentWins = stats.mostFrequentWins === 1 ? "1 win" : `${stats.mostFrequentWins} wins`;
  const streakText = stats.currentStreakTicker
    ? `${stats.currentStreakTicker} streak: ${stats.currentStreakCount}`
    : `${recordCount} records returned`;

  return (
    <section className="summary-grid" aria-label="Dashboard summary">
      <article className="summary-card summary-card-primary">
        <span>Latest top mover</span>
        <h2>{latestTicker}</h2>
        <p className={latestClass}>{latestMove}</p>
        <small>{latestClose}</small>
      </article>

      <article className="summary-card">
        <span>Strongest move</span>
        <h2>{biggestTicker}</h2>
        <p>{biggestMove}</p>
        <small>Largest absolute move in stored history</small>
      </article>

      <article className="summary-card">
        <span>Market mood</span>
        <h2>{stats.marketMood}</h2>
        <p>{stats.gainDays} gain days / {stats.lossDays} loss days</p>
        <small>{recordCount} result{recordCount === 1 ? "" : "s"} returned</small>
      </article>

      <article className="summary-card">
        <span>Frequent winner</span>
        <h2>{frequentTicker}</h2>
        <p>{frequentTicker} leads with {frequentWins}</p>
        <small>{formatNumber(stats.averageAbsoluteMove)}% average move, {streakText}</small>
      </article>
    </section>
  );
}
