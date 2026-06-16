import type { MomentumStats, MoverRecord } from "../types/mover";
import { formatDate, formatPercent, getBarWidth, getTickerClass } from "../utils/formatters";

interface MomentumPanelProps {
  records: MoverRecord[];
  stats: MomentumStats;
}

function getMoodClass(mood: MomentumStats["marketMood"]): string {
  if (mood === "Bullish") {
    return "positive";
  }

  if (mood === "Bearish") {
    return "negative";
  }

  return "neutral";
}

export function MomentumPanel({ records, stats }: MomentumPanelProps) {
  const rankedRecords = [...records]
    .sort((first, second) => Math.abs(second.percent_change) - Math.abs(first.percent_change))
    .slice(0, 4);
  const gainShare = records.length ? (stats.gainDays / records.length) * 100 : 0;
  const lossShare = records.length ? (stats.lossDays / records.length) * 100 : 0;
  const strongestTicker = stats.biggestMover?.ticker ?? "No data";
  const strongestMove = stats.biggestMover ? formatPercent(stats.biggestMover.percent_change) : "0.00%";
  const frequentTicker = stats.mostFrequentTicker ?? "No ticker";
  const frequentWins = stats.mostFrequentWins === 1 ? "1 win" : `${stats.mostFrequentWins} wins`;
  const maxMove = Math.max(...rankedRecords.map((record) => Math.abs(record.percent_change)), 1);

  return (
    <section className="panel momentum-panel">
      <div className="section-heading">
        <h2>Winner intelligence</h2>
        <p>Seven day readout of direction, repeat winners, and strongest stored moves.</p>
      </div>

      <div className="momentum-metrics compact">
        <div>
          <span>Market mood</span>
          <strong className={getMoodClass(stats.marketMood)}>{stats.marketMood}</strong>
          <small>{stats.gainDays} gain days / {stats.lossDays} loss days</small>
        </div>
        <div>
          <span>Frequent winner</span>
          <strong>{frequentTicker}</strong>
          <small>{frequentWins}</small>
        </div>
        <div>
          <span>Strongest mover</span>
          <strong>{strongestTicker}</strong>
          <small>{strongestMove}</small>
        </div>
      </div>

      <div className="mood-meter-block">
        <div className="mood-meter-labels">
          <span>Gain days: {stats.gainDays}</span>
          <span>Loss days: {stats.lossDays}</span>
        </div>
        <div
          className="mood-meter"
          aria-label={`${stats.marketMood} mood: ${stats.gainDays} gain days and ${stats.lossDays} loss days`}
        >
          <span className="mood-meter-gain" style={{ width: `${gainShare}%` }} />
          <span className="mood-meter-loss" style={{ width: `${lossShare}%` }} />
        </div>
      </div>

      {rankedRecords.length > 0 ? (
        <ol className="momentum-rank-list">
          {rankedRecords.map((record) => (
            <li key={`${record.date}-${record.ticker}`}>
              <span>
                <strong>{record.ticker}</strong>
                <small>{formatDate(record.date)}</small>
              </span>
              <span className="mini-track">
                <i className={getTickerClass(record)} style={{ width: getBarWidth(record.percent_change, maxMove) }} />
              </span>
              <span className={getTickerClass(record)}>{formatPercent(record.percent_change)}</span>
            </li>
          ))}
        </ol>
      ) : (
        <p className="empty-copy">No mover records are available for momentum ranking yet.</p>
      )}
    </section>
  );
}
