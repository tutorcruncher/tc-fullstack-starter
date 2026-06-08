import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router';

export type OrderDirection = 'asc' | 'desc';

export type SortState = {
  orderBy?: string;
  orderDirection?: OrderDirection;
};

interface UseOrderParamsOptions {
  /** Also reset `page` to 1 when the sort changes. Defaults to true. */
  resetPageOnChange?: boolean;
}

export interface UseOrderParamsResult {
  sort: SortState;
  setSort: (next: SortState) => void;
  toggleSort: (column: string) => void;
}

/**
 * URL-driven sort state backed by `useSearchParams`. Reads and writes the
 * `order_by` + `order_direction` params, so sort survives reloads, is
 * shareable, and stays the loader's single source of truth. Clicking the same
 * column cycles asc -> desc -> cleared.
 */
export function useOrderParams(options: UseOrderParamsOptions = {}): UseOrderParamsResult {
  const { resetPageOnChange = true } = options;
  const [searchParams, setSearchParams] = useSearchParams();

  const sort = useMemo<SortState>(() => {
    const orderBy = searchParams.get('order_by') || undefined;
    const raw = searchParams.get('order_direction');
    const orderDirection: OrderDirection | undefined =
      raw === 'asc' || raw === 'desc' ? raw : undefined;
    if (!orderBy) {
      return {};
    }
    return { orderBy, orderDirection: orderDirection ?? 'asc' };
  }, [searchParams]);

  const setSort = useCallback(
    (next: SortState): void => {
      setSearchParams(
        (prev) => {
          const params = new URLSearchParams(prev);
          if (next.orderBy) {
            params.set('order_by', next.orderBy);
            params.set('order_direction', next.orderDirection ?? 'asc');
          } else {
            params.delete('order_by');
            params.delete('order_direction');
          }
          if (resetPageOnChange) {
            params.delete('page');
          }
          return params;
        },
        { replace: false },
      );
    },
    [setSearchParams, resetPageOnChange],
  );

  const toggleSort = useCallback(
    (column: string): void => {
      if (sort.orderBy !== column) {
        setSort({ orderBy: column, orderDirection: 'asc' });
      } else if (sort.orderDirection === 'asc') {
        setSort({ orderBy: column, orderDirection: 'desc' });
      } else {
        setSort({});
      }
    },
    [sort, setSort],
  );

  return { sort, setSort, toggleSort };
}
