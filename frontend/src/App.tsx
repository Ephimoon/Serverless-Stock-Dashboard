import { useCallback, useEffect, useMemo, useState } from "react";
import { ErrorState } from "./components/ErrorState";
import { Header } from "./components/Header";
import { LoadingState } from "./components/LoadingState";
import { MomentumPanel } from "./components/MomentumPanel";
import { MoversChart } from "./components/MoversChart";
import { MoversTable } from "./components/MoversTable";
import { ScanList } from "./components/ScanList";
import { SummaryCards } from "./components/SummaryCards";
import { Watchlist } from "./components/Watchlist";
import { fetchMovers } from "./services/moversApi";
import type { MoverRecord } from "./types/mover";
import { calculateMomentum } from "./utils/formatters";

const PAGE_SIZE = 7;

function App() {
  const [records, setRecords] = useState<MoverRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isPaging, setIsPaging] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [currentCursor, setCurrentCursor] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [cursorHistory, setCursorHistory] = useState<(string | null)[]>([]);

  const loadMovers = useCallback(async (cursor: string | null = null, showFullLoading = false) => {
    if (showFullLoading) {
      setIsLoading(true);
    } else {
      setIsPaging(true);
    }

    setErrorMessage(null);

    try {
      const response = await fetchMovers(PAGE_SIZE, cursor);
      setRecords(response.items);
      setCurrentCursor(cursor);
      setNextCursor(response.next_cursor);
      setHasMore(response.has_more);
      return true;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown dashboard error.";
      setErrorMessage(message);
      return false;
    } finally {
      setIsLoading(false);
      setIsPaging(false);
    }
  }, []);

  const loadOlderPage = useCallback(async () => {
    if (!nextCursor || isPaging) {
      return;
    }

    const loaded = await loadMovers(nextCursor);

    if (loaded) {
      setCursorHistory((history) => [...history, currentCursor]);
    }
  }, [currentCursor, isPaging, loadMovers, nextCursor]);

  const loadCurrentPage = useCallback(async () => {
    if (cursorHistory.length === 0 || isPaging) {
      return;
    }

    const loaded = await loadMovers(null);

    if (loaded) {
      setCursorHistory([]);
    }
  }, [cursorHistory.length, isPaging, loadMovers]);

  useEffect(() => {
    void loadMovers(null, true);
  }, [loadMovers]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => window.clearInterval(intervalId);
  }, []);

  const stats = useMemo(() => calculateMomentum(records), [records]);
  const pageNumber = cursorHistory.length + 1;

  return (
    <main className="app-shell">
      <Header
        currentTime={currentTime}
        pageNumber={pageNumber}
        canLoadCurrent={cursorHistory.length > 0}
        canLoadOlder={hasMore}
        isPaging={isPaging}
        onLoadCurrent={loadCurrentPage}
        onLoadOlder={loadOlderPage}
      />

      {isLoading ? <LoadingState /> : null}
      {errorMessage ? <ErrorState message={errorMessage} onRetry={() => void loadMovers(currentCursor, true)} /> : null}

      {!isLoading && !errorMessage ? (
        <>
          <SummaryCards stats={stats} recordCount={records.length} />

          <div className="analysis-grid">
            <Watchlist leaderboard={stats.leaderboard} activeTicker={stats.latestMover?.ticker ?? null} />
            <MomentumPanel records={records} stats={stats} />
          </div>

          <div className="timeline-grid">
            <MoversChart records={records} />
            <ScanList leaderboard={stats.leaderboard} activeTicker={stats.latestMover?.ticker ?? null} />
          </div>

          <MoversTable records={records} />
        </>
      ) : null}
    </main>
  );
}

export default App;
