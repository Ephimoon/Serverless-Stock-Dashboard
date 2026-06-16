import type { WatchlistScore } from "../types/mover";
import { formatDate, getBarWidth } from "../utils/formatters";

interface WatchlistProps {
  leaderboard: WatchlistScore[];
  activeTicker: string | null;
}

export function Watchlist({ leaderboard, activeTicker }: WatchlistProps) {
  const winners = leaderboard.filter((row) => row.wins > 0);
  const maxWins = Math.max(...winners.map((row) => row.wins), 1);

  return (
    <section className="panel leaderboard-panel">
      <div className="section-heading">
        <h2>Watchlist leaderboard</h2>
        <p>Stocks that won the day, ranked by how often they appeared as the daily top mover.</p>
      </div>

      {winners.length > 0 ? (
        <div className="leaderboard-chart">
          {winners.map((row, index) => (
            <div className="leaderboard-row" key={row.ticker}>
              <div className="rank-badge">{index + 1}</div>
              <div className="leaderboard-label">
                <strong className={row.ticker === activeTicker ? "active-ticker" : undefined}>{row.ticker}</strong>
                <span>{row.wins === 1 ? "1 win" : `${row.wins} wins`}</span>
              </div>
              <div className="bar-track" aria-label={`${row.ticker} has ${row.wins} wins`}>
                <div className="bar-fill pennymac-blue" style={{ width: getBarWidth(row.wins, maxWins) }} />
              </div>
              <div className="leaderboard-value">
                <span>Last won</span>
                <strong>{row.latestDate ? formatDate(row.latestDate) : "Stored winner"}</strong>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="empty-copy">No ticker has been stored as a daily winner yet.</p>
      )}
    </section>
  );
}
