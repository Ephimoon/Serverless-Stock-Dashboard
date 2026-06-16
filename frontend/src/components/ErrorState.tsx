interface ErrorStateProps {
  message: string;
  onRetry: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <section className="state-card error-card" role="alert">
      <div>
        <h2>Could not load dashboard data</h2>
        <p>{message}</p>
      </div>
      <button type="button" onClick={onRetry}>Try again</button>
    </section>
  );
}
