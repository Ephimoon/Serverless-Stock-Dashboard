interface HeaderProps {
  lastUpdated: Date | null;
  isRefreshing: boolean;
  onRefresh: () => void;
}

export function Header({ lastUpdated, isRefreshing, onRefresh }: HeaderProps) {
  return (
    <header className="hero-card">
      <div className="hero-copy">
        <p className="eyebrow">AWS Serverless Pipeline</p>
        <h1>Serverless Stock Dashboard</h1>
        <p className="hero-description">
          Tracks a six ticker tech watchlist and shows which stock moved the most each market day.
        </p>
        <div className="hero-meta">
          <span>EventBridge daily scan</span>
          <span>Lambda ingestion</span>
          <span>DynamoDB history</span>
        </div>
      </div>

      <div className="hero-action-card">
        <p>Latest refresh</p>
        <strong>{lastUpdated ? lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "Not loaded"}</strong>
        <button type="button" onClick={onRefresh} disabled={isRefreshing}>
          {isRefreshing ? "Refreshing" : "Refresh data"}
        </button>
      </div>
    </header>
  );
}
