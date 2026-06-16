import { useCallback, useEffect, useMemo, useState } from "react";
import { ErrorState } from "./components/ErrorState";
import { Header } from "./components/Header";
import { LoadingState } from "./components/LoadingState";
import { MoversChart } from "./components/MoversChart";
import { MoversTable } from "./components/MoversTable";
import { SummaryCards } from "./components/SummaryCards";
import { Watchlist } from "./components/Watchlist";
import { fetchMovers } from "./services/moversApi";
import type { MoverRecord } from "./types/mover";
import { calculateMomentum } from "./utils/formatters";

function App() {
  const [records, setRecords] = useState<MoverRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadMovers = useCallback(async (showRefreshState = false) => {
    if (showRefreshState) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }

    setErrorMessage(null);

    try {
      const response = await fetchMovers(7);
      setRecords(response.items);
      setLastUpdated(new Date());
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown dashboard error.";
      setErrorMessage(message);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadMovers();
  }, [loadMovers]);

  const stats = useMemo(() => calculateMomentum(records), [records]);

  return (
    <main className="app-shell">
      <Header
        lastUpdated={lastUpdated}
        isRefreshing={isRefreshing}
        onRefresh={() => void loadMovers(true)}
      />

      {isLoading ? <LoadingState /> : null}
      {errorMessage ? <ErrorState message={errorMessage} onRetry={() => void loadMovers(true)} /> : null}

      {!isLoading && !errorMessage ? (
        <>
          <SummaryCards stats={stats} />
          <div className="dashboard-grid">
            <div className="dashboard-main">
              <MoversChart records={records} />
              <MoversTable records={records} />
            </div>
            <aside className="dashboard-side">
              <Watchlist activeTicker={stats.latestMover?.ticker ?? null} />
              <section className="panel insight-panel">
                <div className="section-heading">
                  <p className="eyebrow">Insight</p>
                  <h2>What this means</h2>
                </div>
                <p>
                  {stats.latestMover
                    ? `${stats.latestMover.ticker} is the latest top mover. The dashboard compares absolute moves, so a large loss can win the day the same way a large gain can.`
                    : "No stored market results are available yet."}
                </p>
              </section>
            </aside>
          </div>
        </>
      ) : null}
    </main>
  );
}

export default App;
