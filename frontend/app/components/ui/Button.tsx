import type { MouseEventHandler, ReactNode } from 'react';
import { Link } from 'react-router';
import { cn } from '~/helpers/cn';

export type ButtonVariant = 'primary' | 'outline' | 'ghost' | 'white';
export type ButtonSize = 'sm' | 'md';

export interface ButtonProps {
  children?: ReactNode;
  /**
   * When set, the button renders as a link: an internal `<Link>` by default, or
   * an external `<a target="_blank">` when {@link ButtonProps.targetBlank} is true.
   */
  href?: string;
  targetBlank?: boolean;
  /** Router navigation state, forwarded to the internal `<Link>`. */
  state?: Record<string, unknown>;
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  type?: 'button' | 'submit' | 'reset';
  disabled?: boolean;
  onClick?: MouseEventHandler<HTMLButtonElement | HTMLAnchorElement>;
  ariaLabel?: string;
  className?: string;
}

const BASE_CLASSES =
  'inline-flex items-center justify-center whitespace-nowrap rounded-full font-medium transition cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50';

const SIZE_CLASSES: Record<ButtonSize, string> = {
  sm: 'px-3.5 py-1.5 gap-1.5 text-small',
  md: 'px-5 py-2 gap-2 text-body',
};

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary: 'bg-primary text-white border border-transparent hover:bg-primary-dark',
  outline: 'bg-white text-neutral-900 border border-neutral-200 hover:bg-neutral-50',
  ghost: 'bg-transparent text-neutral-700 border border-transparent hover:bg-neutral-100',
  white: 'bg-white text-neutral-900 border border-neutral-200 hover:bg-neutral-50',
};

const DISABLED_CLASSES =
  'opacity-60 text-neutral-500 bg-neutral-100 border border-neutral-200 cursor-not-allowed';

/**
 * Polymorphic button. Renders an internal `<Link>` for `href`, an external
 * `<a target="_blank">` for `href` + `targetBlank`, otherwise a `<button>`.
 * Styling comes from variant/size maps composed via {@link cn}.
 */
export function Button({
  children,
  href,
  targetBlank = false,
  state,
  variant = 'primary',
  size = 'md',
  icon,
  iconPosition = 'left',
  type = 'button',
  disabled = false,
  onClick,
  ariaLabel,
  className,
}: ButtonProps) {
  const classes = cn(
    BASE_CLASSES,
    SIZE_CLASSES[size],
    disabled ? DISABLED_CLASSES : VARIANT_CLASSES[variant],
    className,
  );

  const content = (
    <>
      {iconPosition === 'left' && icon}
      {children}
      {iconPosition === 'right' && icon}
    </>
  );

  if (href && !disabled) {
    if (targetBlank) {
      return (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className={classes}
          aria-label={ariaLabel}
          onClick={onClick}
        >
          {content}
        </a>
      );
    }
    return (
      <Link to={href} state={state} className={classes} aria-label={ariaLabel} onClick={onClick}>
        {content}
      </Link>
    );
  }

  return (
    <button
      type={type}
      className={classes}
      disabled={disabled}
      aria-label={ariaLabel}
      onClick={onClick}
    >
      {content}
    </button>
  );
}
