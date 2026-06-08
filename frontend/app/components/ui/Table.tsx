import type { Key, KeyboardEvent, MouseEvent, ReactNode } from 'react';
import { useNavigate } from 'react-router';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '~/helpers/cn';
import type { OrderDirection, SortState } from '~/hooks/useOrderParams';
import { Pagination } from './Pagination';

export interface Column<T> {
  /** Column header label. */
  header: string;
  /** Renders the cell for a row. */
  cell: (row: T) => ReactNode;
  /** If set, the header becomes a sort toggle for this backend field. */
  sortKey?: string;
  /** Right-align the header and cells (e.g. an actions column). */
  align?: 'left' | 'right';
}

export interface TableProps<T> {
  columns: Column<T>[];
  rows: T[];
  /** Stable React key per row. Falls back to the row index. */
  getRowKey?: (row: T) => Key;
  /** Fallback shown when `rows` is empty. */
  emptyMessage?: string;
  /** Current sort state; pair with {@link TableProps.onSortChange} to enable sorting. */
  sort?: SortState;
  /** Called with the column's `sortKey` when a sortable header is activated. */
  onSortChange?: (sortKey: string) => void;
  /** If set, rows become navigable (Enter / click; cmd/ctrl/middle-click opens a new tab). */
  getRowHref?: (row: T) => string;
  /** Total items across all pages — enables an embedded {@link Pagination}. */
  total?: number;
  /** Current page (1-indexed). Defaults to 1. */
  page?: number;
  /** Items per page. Defaults to `total`. */
  pageSize?: number;
  /** Called when the embedded pagination changes page. */
  onPageChange?: (page: number) => void;
}

const WRAPPER_CLASSES = 'overflow-hidden rounded-2xl border border-neutral-200 bg-white';
const HEAD_CLASSES =
  'border-b border-neutral-200 bg-neutral-50 text-small uppercase tracking-wide text-neutral-500';
const TH_BASE = 'px-4 py-2.5 font-medium';
const TD_BASE = 'px-4 py-3 align-middle';

function SortIndicator({ direction }: { direction: OrderDirection | 'none' }) {
  if (direction === 'asc') {
    return <ChevronUp className="ml-1.5 h-3 w-3 text-neutral-900" aria-hidden />;
  }
  if (direction === 'desc') {
    return <ChevronDown className="ml-1.5 h-3 w-3 text-neutral-900" aria-hidden />;
  }
  return <ChevronDown className="ml-1.5 h-3 w-3 text-neutral-300" aria-hidden />;
}

/**
 * Generic, strongly-typed table. Declare a `Column<T>[]` and pass `rows`.
 * Optional features: column sorting (`sort` + `onSortChange`, with `aria-sort`
 * headers), navigable rows (`getRowHref`), and an embedded {@link Pagination}
 * (`total`/`page`/`pageSize`/`onPageChange`).
 */
export function Table<T>({
  columns,
  rows,
  getRowKey,
  emptyMessage,
  sort,
  onSortChange,
  getRowHref,
  total,
  page = 1,
  pageSize,
  onPageChange,
}: TableProps<T>) {
  const navigate = useNavigate();

  const handleRowActivate =
    (href: string) =>
    (event: MouseEvent): void => {
      const target = event.target as HTMLElement;
      if (target.closest('a, button, input, select, textarea, label, [role="button"]')) {
        return;
      }
      if (event.metaKey || event.ctrlKey || event.button === 1) {
        window.open(href, '_blank', 'noopener,noreferrer');
        return;
      }
      if (event.button === 0) {
        navigate(href);
      }
    };

  const handleRowKey =
    (href: string) =>
    (event: KeyboardEvent): void => {
      if (event.key === 'Enter') {
        event.preventDefault();
        navigate(href);
      }
    };

  if (rows.length === 0 && emptyMessage) {
    return (
      <div className={WRAPPER_CLASSES}>
        <div className="px-6 py-10 text-center text-neutral-500">{emptyMessage}</div>
      </div>
    );
  }

  const effectiveTotal = total ?? rows.length;
  const effectivePageSize = pageSize ?? Math.max(effectiveTotal, 1);
  const totalPages = Math.max(1, Math.ceil(effectiveTotal / effectivePageSize));

  return (
    <div className={WRAPPER_CLASSES}>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-body">
          <thead className={HEAD_CLASSES}>
            <tr>
              {columns.map((col, i) => {
                const sortable = !!col.sortKey && !!onSortChange;
                const active = sortable && sort?.orderBy === col.sortKey;
                const direction: OrderDirection | 'none' = active
                  ? (sort?.orderDirection ?? 'asc')
                  : 'none';
                const thClass = cn(TH_BASE, col.align === 'right' ? 'text-right' : 'text-left');

                if (!sortable || !col.sortKey) {
                  return (
                    <th key={i} className={thClass} scope="col">
                      {col.header}
                    </th>
                  );
                }

                const sortKey = col.sortKey;
                return (
                  <th
                    key={i}
                    className={thClass}
                    scope="col"
                    aria-sort={active ? (direction === 'asc' ? 'ascending' : 'descending') : 'none'}
                  >
                    <button
                      type="button"
                      onClick={() => onSortChange(sortKey)}
                      className={cn(
                        'inline-flex items-center font-medium uppercase tracking-wide transition',
                        'hover:text-neutral-900 focus:outline-none focus-visible:underline',
                        col.align === 'right' && 'flex-row-reverse',
                        active && 'text-neutral-900',
                      )}
                    >
                      {col.header}
                      <SortIndicator direction={direction} />
                    </button>
                  </th>
                );
              })}
            </tr>
          </thead>

          <tbody className="divide-y divide-neutral-100">
            {rows.map((row, i) => {
              const href = getRowHref?.(row);
              return (
                <tr
                  key={getRowKey?.(row) ?? i}
                  className={cn('transition-colors hover:bg-neutral-50', href && 'cursor-pointer')}
                  onClick={href ? handleRowActivate(href) : undefined}
                  onAuxClick={href ? handleRowActivate(href) : undefined}
                  onKeyDown={href ? handleRowKey(href) : undefined}
                  tabIndex={href ? 0 : undefined}
                  role={href ? 'link' : undefined}
                >
                  {columns.map((col, j) => (
                    <td
                      key={j}
                      className={cn(TD_BASE, col.align === 'right' ? 'text-right' : 'text-left')}
                    >
                      {col.cell(row)}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {total !== undefined && (
        <Pagination
          total={effectiveTotal}
          page={Math.min(Math.max(1, page), totalPages)}
          pageSize={effectivePageSize}
          totalPages={totalPages}
          onChange={onPageChange}
        />
      )}
    </div>
  );
}
