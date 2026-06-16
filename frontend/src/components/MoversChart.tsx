import { useMemo } from "react";
import type { MoverRecord } from "../types/mover";
import { formatDate, formatPercent, getBarWidth, getTickerClass } from "../utils/formatters";

interface MoversChartProps {
  records: MoverRecord[];
}

function getMaxWinnerMove(records: MoverRecord[]): number {
  return Math.max(...records.map((record) => Math.abs(record.percent_change)), 1);
}

export function MoversChart({ records }: MoversChartProps) {
  const maxWinnerMove = useMemo(() => getMaxWinnerMove(records), [records]);

  return (
    <section className="panel chart-panel">
      <div className="section-heading">
        <h2>Daily winner timeline</h2>
        <p>Each bar is one stored daily winner. Bar length uses absolute percent change, so losses and gains are compared evenly.</p>
      </div>

      {records.length > 0 ? (
        <div className="bar-list">
          {records.map((record) => (
            <div className="bar-row" key={`${record.date}-${record.ticker}`}>
              <div className="bar-label">
                <strong>{record.ticker}</strong>
                <span>{formatDate(record.date)}</span>
              </div>
              <div className="bar-track" aria-label={`${record.ticker} moved ${formatPercent(record.percent_change)}`}>
                <div
                  className={`bar-fill ${getTickerClass(record)}`}
                  style={{ width: getBarWidth(record.percent_change, maxWinnerMove) }}
                />
              </div>
              <span className={`bar-value ${getTickerClass(record)}`}>{formatPercent(record.percent_change)}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="empty-copy">No stored daily winners are available for the timeline yet.</p>
      )}
    </section>
  );
}
