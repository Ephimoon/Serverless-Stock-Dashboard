import { watchlist } from "../utils/formatters";

interface WatchlistProps {
  activeTicker: string | null;
}

export function Watchlist({ activeTicker }: WatchlistProps) {
  return (
    <section className="panel watchlist-panel">
      <div className="section-heading">
        <p className="eyebrow">Watchlist</p>
        <h2>Tracked tickers</h2>
      </div>
      <div className="watchlist-grid" aria-label="Tracked stock ticker list">
        {watchlist.map((ticker) => (
          <span className={ticker === activeTicker ? "ticker-pill active" : "ticker-pill"} key={ticker}>
            {ticker}
          </span>
        ))}
      </div>
    </section>
  );
}
