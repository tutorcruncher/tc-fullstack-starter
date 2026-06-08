import { AlertTriangle } from 'lucide-react';
import { Heading } from './Heading';
import { Button } from './Button';

export interface ErrorStateProps {
  /** The error message to display. */
  message: string;
  /** Optional retry handler — renders a "Try again" button when provided. */
  onRetry?: () => void;
}

/**
 * Error message with an optional retry action. Rendered by the root
 * `ErrorBoundary` and on failed client-side fetches.
 */
export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex min-h-full items-center justify-center p-8" role="alert">
      <div className="max-w-md text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-error-soft text-error">
          <AlertTriangle className="h-[18px] w-[18px]" aria-hidden />
        </div>
        <Heading level={2} as="h2" noMargin>
          Something went wrong
        </Heading>
        <p className="mt-2 text-neutral-500">{message}</p>
        {onRetry && (
          <Button variant="outline" size="sm" className="mt-4" onClick={onRetry}>
            Try again
          </Button>
        )}
      </div>
    </div>
  );
}
