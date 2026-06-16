import { watchlist } from "../utils/formatters";

interface HeaderProps {
  currentTime: Date;
  pageNumber: number;
  canLoadCurrent: boolean;
  canLoadOlder: boolean;
  isPaging: boolean;
  onLoadCurrent: () => void;
  onLoadOlder: () => void;
}

export function Header({
  currentTime,
  pageNumber,
  canLoadCurrent,
  canLoadOlder,
  isPaging,
  onLoadCurrent,
  onLoadOlder,
}: HeaderProps) {
  const currentLabel = currentTime.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <header className="app-header">
      <div className="brand-row">
        <div className="header-copy">
          <h1>Serverless Stock Dashboard</h1>
          <p>
            Daily AWS pipeline that stores the biggest watchlist mover in DynamoDB
            and serves paginated winner history through GET /movers.
          </p>
        </div>

        <div className="header-actions" aria-label="Dashboard controls">
          <div className="header-clock" aria-label="Current time">
            <span>Live clock</span>
            <strong>{currentLabel}</strong>
          </div>

          <div className="header-pagination" aria-label="History pagination">
            <span>History page</span>

            <div className="header-pagination-row">
              <button type="button" onClick={onLoadOlder} disabled={!canLoadOlder || isPaging}>
                Older
              </button>

              <strong>{isPaging ? "Loading" : `Page ${pageNumber}`}</strong>

              <button type="button" onClick={onLoadCurrent} disabled={!canLoadCurrent || isPaging}>
                Current
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="header-watchlist" aria-label="Tracked watchlist">
        {watchlist.map((ticker) => (
          <span key={ticker}>{ticker}</span>
        ))}
      </div>
    </header>
  );
}