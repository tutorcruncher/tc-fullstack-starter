export interface LoadingStateProps {
  /** Accessible label announced to assistive tech and shown beneath the spinner. */
  label?: string;
}

/** Centered spinner for pending UI (route fallbacks, in-flight fetches). */
export function LoadingState({ label = 'Loading…' }: LoadingStateProps) {
  return (
    <div
      className="flex min-h-full items-center justify-center p-8"
      role="status"
      aria-live="polite"
    >
      <div className="text-center">
        <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-[3px] border-neutral-200 border-t-primary" />
        <p className="text-neutral-500">{label}</p>
      </div>
    </div>
  );
}
