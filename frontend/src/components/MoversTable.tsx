import { useMemo, useState } from "react";
import type { MoverRecord } from "../types/mover";
import { formatCurrency, formatDate, formatPercent, getMoverDirection, getTickerClass } from "../utils/formatters";

interface MoversTableProps {
  records: MoverRecord[];
}

type HistoryView = "table" | "trend";

interface TrendPoint {
  record: MoverRecord;
  x: number;
  y: number;
  textY: number;
  dateY: number;
  anchor: "start" | "middle" | "end";
}

function getTrendPoints(records: MoverRecord[]): TrendPoint[] {
  if (records.length === 0) {
    return [];
  }

  const chronologicalRecords = [...records].reverse();
  const maxMove = Math.max(...chronologicalRecords.map((record) => Math.abs(record.percent_change)), 1);
  const left = 24;
  const right = 148;
  const centerY = 39;
  const rangeY = 24;

  return chronologicalRecords.map((record, index) => {
    const x = chronologicalRecords.length === 1
      ? (left + right) / 2
      : left + (index / (chronologicalRecords.length - 1)) * (right - left);
    const y = centerY - (record.percent_change / maxMove) * rangeY;
    const textY = record.percent_change >= 0 ? Math.max(y - 4, 8) : Math.min(y + 6, 66);
    const dateY = 77;
    const anchor = index === 0 ? "start" : index === chronologicalRecords.length - 1 ? "end" : "middle";

    return { record, x, y, textY, dateY, anchor };
  });
}

function formatShortDate(value: string): string {
  const date = new Date(`${value}T00:00:00Z`);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  }).format(date);
}

export function MoversTable({ records }: MoversTableProps) {
  const [view, setView] = useState<HistoryView>("table");
  const trendPoints = useMemo(() => getTrendPoints(records), [records]);
  const chronologicalRecords = useMemo(() => [...records].reverse(), [records]);
  const maxMove = Math.max(...chronologicalRecords.map((record) => Math.abs(record.percent_change)), 1);
  const polylinePoints = trendPoints.map((point) => `${point.x.toFixed(2)},${point.y.toFixed(2)}`).join(" ");
  const topLabel = formatPercent(maxMove).replace("+", "");
  const bottomLabel = formatPercent(-maxMove);

  return (
    <section className="panel table-panel">
      <div className="section-heading heading-with-action">
        <div>
          <h2>Daily winner history</h2>
          <p>The API returns the last seven daily winners stored in DynamoDB.</p>
        </div>

        <div className="view-toggle" aria-label="History view toggle">
          <button
            className={view === "table" ? "active" : undefined}
            type="button"
            onClick={() => setView("table")}
          >
            Table
          </button>
          <button
            className={view === "trend" ? "active" : undefined}
            type="button"
            onClick={() => setView("trend")}
          >
            Trend
          </button>
        </div>
      </div>

      {records.length === 0 ? (
        <p className="empty-copy">No mover records have been stored yet.</p>
      ) : view === "table" ? (
        <div className="table-wrap">
          <table>
            <caption className="sr-only">Top mover history returned by GET /movers</caption>
            <thead>
              <tr>
                <th>Date</th>
                <th>Ticker</th>
                <th>Percent change</th>
                <th>Closing price</th>
                <th>Direction</th>
              </tr>
            </thead>
            <tbody>
              {records.map((record) => (
                <tr key={`${record.date}-${record.ticker}`}>
                  <td>{formatDate(record.date)}</td>
                  <td><span className="ticker-symbol">{record.ticker}</span></td>
                  <td className={getTickerClass(record)}>{formatPercent(record.percent_change)}</td>
                  <td>{formatCurrency(record.close_price)}</td>
                  <td>
                    <span className={`direction-badge ${getTickerClass(record)}`}>
                      {getMoverDirection(record) === "up" ? "Gain" : "Loss"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="trend-panel" aria-label="Daily winner percent change trend">
          <svg viewBox="0 0 160 86" role="img" aria-label="Percent change trend line">
            <text className="trend-axis-title y-axis-title" x="5" y="40" transform="rotate(-90 5 40)">
              Percent change
            </text>
            <text className="trend-axis-title x-axis-title" x="86" y="84" textAnchor="middle">
              Market date
            </text>

            <line className="trend-grid-line" x1="22" x2="150" y1="15" y2="15" />
            <line className="trend-zero-line" x1="22" x2="150" y1="39" y2="39" />
            <line className="trend-grid-line" x1="22" x2="150" y1="63" y2="63" />
            <text className="trend-axis-label" x="9" y="16">+{topLabel}</text>
            <text className="trend-axis-label" x="11" y="40.2">0%</text>
            <text className="trend-axis-label" x="9" y="64">{bottomLabel}</text>

            <polyline points={polylinePoints} />

            {trendPoints.map(({ record, x, y, textY, dateY, anchor }) => (
              <g key={`${record.date}-${record.ticker}`}>
                <circle
                  className={getTickerClass(record)}
                  cx={x}
                  cy={y}
                  r="1.9"
                />
                <text
                  className={`trend-point-label ${getTickerClass(record)}`}
                  x={x}
                  y={textY}
                  textAnchor={anchor}
                >
                  {formatPercent(record.percent_change)}
                </text>
                <text
                  className="trend-date-label"
                  x={x}
                  y={dateY}
                  textAnchor="middle"
                  transform={`rotate(-28 ${x} ${dateY})`}
                >
                  {record.ticker} {formatShortDate(record.date)}
                </text>
              </g>
            ))}
          </svg>
        </div>
      )}
    </section>
  );
}
