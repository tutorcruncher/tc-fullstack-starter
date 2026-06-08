import type { ReactNode } from 'react';
import { cn } from '~/helpers/cn';

export interface CardProps {
  children: ReactNode;
  /** Add a subtle hover background. Useful for navigable cards. */
  hover?: boolean;
  /** Override the default background utility (default `bg-white`). */
  bgClassName?: string;
  className?: string;
}

/** Rounded, bordered surface container. The generic building block for panels. */
export function Card({ children, hover = false, bgClassName = 'bg-white', className }: CardProps) {
  return (
    <div
      className={cn(
        'flex flex-col rounded-2xl border border-neutral-200 p-5',
        bgClassName,
        hover && 'transition hover:bg-neutral-50',
        className,
      )}
    >
      {children}
    </div>
  );
}
