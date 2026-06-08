import { useMemo } from 'react';
import { cn } from '~/helpers/cn';

export interface PaginationProps {
  /** Total number of items across all pages. */
  total: number;
  /** Current page (1-indexed). */
  page: number;
  /** Items per page. */
  pageSize: number;
  /** Total number of pages. */
  totalPages: number;
  /** Called with the next page when the user navigates. Read-only if omitted. */
  onChange?: (page: number) => void;
}

const DELTA = 2;

/** Build a page list with `'ellipsis'` gaps, always keeping the first/last page. */
function getPageNumbers(current: number, total: number): (number | 'ellipsis')[] {
  const range: number[] = [];
  for (let i = 1; i <= total; i++) {
    if (i === 1 || i === total || (i >= current - DELTA && i <= current + DELTA)) {
      range.push(i);
    }
  }

  const withDots: (number | 'ellipsis')[] = [];
  let prev: number | undefined;
  for (const i of range) {
    if (prev !== undefined && i - prev > 1) {
      withDots.push('ellipsis');
    }
    withDots.push(i);
    prev = i;
  }
  return withDots;
}

const PAGE_BTN_BASE =
  'inline-flex h-8 min-w-[32px] items-center justify-center rounded-full px-2.5 transition';
const PAGE_BTN_INACTIVE = 'border border-neutral-200 bg-white text-neutral-900 hover:bg-neutral-50';
const PAGE_BTN_ACTIVE = 'border border-primary bg-primary text-white hover:bg-primary-dark';
const PAGE_BTN_DISABLED =
  'border border-neutral-200 bg-white text-neutral-500 opacity-60 cursor-not-allowed';

/**
 * Page-range pagination with ellipsis gaps and a "Showing X–Y of Z" summary.
 * Returns `null` when there is a single page or fewer. Used standalone or
 * embedded inside {@link Table}.
 */
export function Pagination({ total, page, pageSize, totalPages, onChange }: PaginationProps) {
  const pageNumbers = useMemo(() => getPageNumbers(page, totalPages), [page, totalPages]);

  if (totalPages <= 1) {
    return null;
  }

  const startIdx = total > 0 ? (page - 1) * pageSize + 1 : 0;
  const endIdx = Math.min(page * pageSize, total);
  const go = (next: number) => (): void => onChange?.(next);

  return (
    <div className="flex items-center justify-between border-t border-neutral-200 px-5 py-3.5">
      <p className="text-small text-neutral-500">
        Showing <span className="text-neutral-900">{startIdx}</span>–
        <span className="text-neutral-900">{endIdx}</span> of{' '}
        <span className="text-neutral-900">{total}</span>
      </p>

      <nav className="flex items-center gap-1.5" aria-label="Pagination">
        <button
          type="button"
          onClick={go(page - 1)}
          disabled={page <= 1}
          aria-label="Previous page"
          className={cn(PAGE_BTN_BASE, page <= 1 ? PAGE_BTN_DISABLED : PAGE_BTN_INACTIVE)}
        >
          ‹
        </button>
        {pageNumbers.map((p, idx) =>
          p === 'ellipsis' ? (
            <span key={`ellipsis-${idx}`} className="px-1.5 text-neutral-500">
              …
            </span>
          ) : (
            <button
              key={p}
              type="button"
              onClick={go(p)}
              aria-current={p === page ? 'page' : undefined}
              className={cn(PAGE_BTN_BASE, p === page ? PAGE_BTN_ACTIVE : PAGE_BTN_INACTIVE)}
            >
              {p}
            </button>
          ),
        )}
        <button
          type="button"
          onClick={go(page + 1)}
          disabled={page >= totalPages}
          aria-label="Next page"
          className={cn(PAGE_BTN_BASE, page >= totalPages ? PAGE_BTN_DISABLED : PAGE_BTN_INACTIVE)}
        >
          ›
        </button>
      </nav>
    </div>
  );
}
