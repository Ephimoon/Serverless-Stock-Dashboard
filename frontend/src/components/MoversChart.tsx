import type { MoverRecord } from "../types/mover";
import { formatDate, formatPercent, getBarWidth, getTickerClass } from "../utils/formatters";

interface MoversChartProps {
  records: MoverRecord[];
}

export function MoversChart({ records }: MoversChartProps) {
  if (records.length === 0) {
    return null;
  }

  return (
    <section className="panel chart-panel">
      <div className="section-heading">
        <p className="eyebrow">Creative feature</p>
        <h2>Mover momentum</h2>
        <p>Bar width is based on absolute percent change, so losses and gains are compared evenly.</p>
      </div>

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
                style={{ width: getBarWidth(record, records) }}
              />
            </div>
            <span className={`bar-value ${getTickerClass(record)}`}>{formatPercent(record.percent_change)}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
