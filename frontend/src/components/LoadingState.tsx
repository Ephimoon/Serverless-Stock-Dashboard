export function LoadingState() {
  return (
    <section className="state-card" aria-live="polite">
      <div className="spinner" />
      <div>
        <h2>Loading stock movers</h2>
        <p>Fetching the latest winners from the API Gateway endpoint.</p>
      </div>
    </section>
  );
}
