import type { MoverRecord } from "../types/mover";
import { formatCurrency, formatDate, formatPercent, getTickerClass } from "../utils/formatters";

interface MoversTableProps {
  records: MoverRecord[];
}

export function MoversTable({ records }: MoversTableProps) {
  return (
    <section className="panel table-panel">
      <div className="section-heading">
        <p className="eyebrow">History</p>
        <h2>Top mover results</h2>
        <p>The API returns the latest winning stocks stored in DynamoDB.</p>
      </div>

      <div className="table-wrap">
        <table>
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
                    {record.direction === "up" ? "Gain" : "Loss"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
