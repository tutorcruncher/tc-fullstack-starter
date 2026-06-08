import { AlertCircle, AlertTriangle, CheckCircle, Info, type LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';
import { cn } from '~/helpers/cn';

export type AlertVariant = 'danger' | 'warning' | 'info' | 'success';

export interface AlertProps {
  children: ReactNode;
  variant?: AlertVariant;
  /** Override the auto icon, or pass `false` to hide it. */
  icon?: LucideIcon | false;
  className?: string;
}

const VARIANT_CLASSES: Record<AlertVariant, string> = {
  danger: 'bg-error-soft border-error-soft text-error',
  warning: 'bg-warning-soft border-warning-soft text-warning',
  info: 'bg-info-soft border-info-soft text-info',
  success: 'bg-success-soft border-success-soft text-success',
};

const VARIANT_ICONS: Record<AlertVariant, LucideIcon> = {
  danger: AlertCircle,
  warning: AlertTriangle,
  info: Info,
  success: CheckCircle,
};

/** Inline status message with an auto icon per variant. Announced via `role="alert"`. */
export function Alert({ children, variant = 'danger', icon, className }: AlertProps) {
  const IconComponent = icon === false ? null : (icon ?? VARIANT_ICONS[variant]);

  return (
    <div
      role="alert"
      className={cn(
        'flex items-start gap-3 rounded-md border px-4 py-3 text-body',
        VARIANT_CLASSES[variant],
        className,
      )}
    >
      {IconComponent && <IconComponent className="mt-0.5 h-5 w-5 shrink-0" strokeWidth={2} />}
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}
