import { useCallback, useState } from 'react';

type AsyncFn<TArgs extends unknown[], TResult> = (...args: TArgs) => Promise<TResult>;

export interface UseAsyncActionResult<TArgs extends unknown[], TResult> {
  isLoading: boolean;
  error: string | null;
  execute: (...args: TArgs) => Promise<TResult | undefined>;
  reset: () => void;
}

/**
 * Wraps a client-side async mutation with the standard loading + error
 * scaffolding: sets `isLoading` true while the action runs, captures any thrown
 * error as a string, and always clears the loading flag at the end.
 *
 * `execute` resolves to `undefined` on failure so callers can branch on the
 * resolved value instead of re-implementing try/catch. Prefer route actions for
 * navigations; reach for this only for in-place mutations (e.g. inside a Modal).
 */
export function useAsyncAction<TArgs extends unknown[], TResult>(
  action: AsyncFn<TArgs, TResult>,
): UseAsyncActionResult<TArgs, TResult> {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(
    async (...args: TArgs): Promise<TResult | undefined> => {
      setIsLoading(true);
      setError(null);
      try {
        return await action(...args);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Something went wrong');
        return undefined;
      } finally {
        setIsLoading(false);
      }
    },
    [action],
  );

  const reset = useCallback(() => {
    setIsLoading(false);
    setError(null);
  }, []);

  return { isLoading, error, execute, reset };
}
