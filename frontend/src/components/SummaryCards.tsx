import type { MomentumStats } from "../types/mover";
import { formatCurrency, formatNumber, formatPercent } from "../utils/formatters";

interface SummaryCardsProps {
  stats: MomentumStats;
}

export function SummaryCards({ stats }: SummaryCardsProps) {
  const latestClass = stats.latestMover ? (stats.latestMover.direction === "up" ? "positive" : "negative") : undefined;
  const latestTicker = stats.latestMover?.ticker ?? "No data";
  const latestMove = stats.latestMover ? formatPercent(stats.latestMover.percent_change) : "0.00%";
  const biggestTicker = stats.biggestMover?.ticker ?? "No data";
  const biggestMove = stats.biggestMover ? formatPercent(stats.biggestMover.percent_change) : "0.00%";
  const closePrice = stats.latestMover ? formatCurrency(stats.latestMover.close_price) : "$0.00";

  return (
    <section className="summary-grid" aria-label="Dashboard summary">
      <article className="summary-card highlight-card">
        <span>Latest winner</span>
        <h2>{latestTicker}</h2>
        <p className={latestClass}>{latestMove}</p>
        <small>Close price {closePrice}</small>
      </article>

      <article className="summary-card">
        <span>Biggest move</span>
        <h2>{biggestTicker}</h2>
        <p>{biggestMove}</p>
        <small>Largest absolute move in the current history</small>
      </article>

      <article className="summary-card">
        <span>Market mood</span>
        <h2>{stats.marketMood}</h2>
        <p>{stats.gainDays} gain days · {stats.lossDays} loss days</p>
        <small>Based on the latest movers returned by the API</small>
      </article>

      <article className="summary-card">
        <span>Average move</span>
        <h2>{formatNumber(stats.averageAbsoluteMove)}%</h2>
        <p>{stats.mostFrequentTicker ?? "No ticker"} leads with {stats.mostFrequentWins} win</p>
        <small>
          {stats.currentStreakTicker
            ? `${stats.currentStreakTicker} current streak: ${stats.currentStreakCount}`
            : "No active streak"}
        </small>
      </article>
    </section>
  );
}
