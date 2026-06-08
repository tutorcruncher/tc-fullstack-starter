import type { ReactNode } from 'react';
import { cn } from '~/helpers/cn';

type HeadingLevel = 1 | 2 | 3 | 4 | 5 | 6;
type HeadingTag = 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';

export interface HeadingProps {
  children: ReactNode;
  /** Visual size, mapped to a `text-*` token. Defaults to 1. */
  level?: HeadingLevel;
  /** Semantic tag. Defaults to `h{level}` — set this to keep the document outline correct. */
  as?: HeadingTag;
  noMargin?: boolean;
  id?: string;
  className?: string;
}

const SIZE_CLASSES: Record<HeadingLevel, string> = {
  1: 'text-h1 font-semibold',
  2: 'text-h2 font-semibold',
  3: 'text-h3 font-semibold',
  4: 'text-body font-semibold',
  5: 'text-body font-medium',
  6: 'text-small font-medium uppercase tracking-wide',
};

const MARGIN_CLASSES: Record<HeadingLevel, string> = {
  1: 'mb-4',
  2: 'mb-3',
  3: 'mb-2',
  4: 'mb-2',
  5: 'mb-1',
  6: 'mb-1',
};

/**
 * Separates visual size (`level` → `text-*` token) from the semantic tag (`as`).
 * Always prefer this over raw `<h1>`–`<h6>` so typography stays consistent.
 */
export function Heading({
  children,
  level = 1,
  as,
  noMargin = false,
  id,
  className,
}: HeadingProps) {
  const Tag = as ?? (`h${level}` as HeadingTag);

  return (
    <Tag
      id={id}
      className={cn(
        SIZE_CLASSES[level],
        !noMargin && MARGIN_CLASSES[level],
        'text-neutral-900',
        className,
      )}
    >
      {children}
    </Tag>
  );
}
