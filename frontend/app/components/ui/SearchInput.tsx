import type { FormEvent, RefObject } from 'react';
import { cn } from '~/helpers/cn';
import { Search, Spinner } from '~/components/icons/Icon';

export interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  placeholder?: string;
  loading?: boolean;
  inputRef?: RefObject<HTMLInputElement | null>;
  className?: string;
}

/**
 * Form-wrapped search field with a leading icon that swaps to a spinner while
 * `loading`. Submitting (Enter) calls `onSubmit`; the caller owns the query
 * state (typically URL-driven via `useSearchParams`).
 */
export function SearchInput({
  value,
  onChange,
  onSubmit,
  placeholder = 'Search…',
  loading = false,
  inputRef,
  className,
}: SearchInputProps) {
  return (
    <form
      onSubmit={onSubmit}
      role="search"
      className={cn('relative w-full max-w-md min-w-[240px]', className)}
    >
      <span className="pointer-events-none absolute top-1/2 left-3 flex h-3.5 w-3.5 -translate-y-1/2 items-center justify-center text-neutral-500">
        {loading ? <Spinner size={14} className="animate-spin" /> : <Search size={14} />}
      </span>
      <input
        ref={inputRef}
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        aria-label={placeholder}
        aria-busy={loading}
        className="w-full rounded-xl border border-neutral-200 bg-white py-2 pr-3 pl-9 text-body outline-none transition focus:border-primary"
      />
    </form>
  );
}
