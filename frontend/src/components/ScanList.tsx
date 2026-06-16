import type { WatchlistScore } from "../types/mover";
import { formatDate, formatPercent, watchlist } from "../utils/formatters";

interface ScanListProps {
  leaderboard: WatchlistScore[];
  activeTicker: string | null;
}

export function ScanList({ leaderboard, activeTicker }: ScanListProps) {
  const scoreByTicker = new Map(leaderboard.map((row) => [row.ticker, row]));

  return (
    <section className="panel scan-list-panel">
      <div className="section-heading">
        <h2>Daily Lambda watchlist</h2>
        <p>The scheduled job evaluates all six tickers, then stores only the single largest absolute mover.</p>
      </div>

      <div className="scan-list">
        {watchlist.map((ticker) => {
          const score = scoreByTicker.get(ticker);
          const hasWon = Boolean(score && score.wins > 0);

          return (
            <article className={ticker === activeTicker ? "active" : undefined} key={ticker}>
              <div>
                <strong>{ticker}</strong>
                <span>{hasWon ? `${score?.wins} ${score?.wins === 1 ? "win" : "wins"}` : "No wins yet"}</span>
              </div>
              <small>
                {score?.latestDate && score.latestMove !== null
                  ? `${formatPercent(score.latestMove)} on ${formatDate(score.latestDate)}`
                  : "Still evaluated each scheduled run"}
              </small>
            </article>
          );
        })}
      </div>
    </section>
  );
}
