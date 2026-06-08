import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { AlertCircle, CheckCircle2, Info, X, type LucideIcon } from 'lucide-react';
import { cn } from '~/helpers/cn';

export type ToastType = 'success' | 'error' | 'info';

export interface ToastItem {
  id: string;
  message: string;
  type: ToastType;
  duration?: number;
}

interface ToastContextValue {
  toasts: ToastItem[];
  showToast: (message: string, type?: ToastType, duration?: number) => void;
  showSuccess: (message: string, duration?: number) => void;
  showError: (message: string, duration?: number) => void;
  showInfo: (message: string, duration?: number) => void;
  removeToast: (id: string) => void;
}

const DEFAULT_DURATION = 3000;

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string): void => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback(
    (message: string, type: ToastType = 'info', duration: number = DEFAULT_DURATION): void => {
      const toast: ToastItem = { id: crypto.randomUUID(), message, type, duration };
      setToasts((prev) => [...prev, toast]);
    },
    [],
  );

  const showSuccess = useCallback(
    (message: string, duration?: number): void => showToast(message, 'success', duration),
    [showToast],
  );

  const showError = useCallback(
    (message: string, duration?: number): void => showToast(message, 'error', duration),
    [showToast],
  );

  const showInfo = useCallback(
    (message: string, duration?: number): void => showToast(message, 'info', duration),
    [showToast],
  );

  const value = useMemo<ToastContextValue>(
    () => ({ toasts, showToast, showSuccess, showError, showInfo, removeToast }),
    [toasts, showToast, showSuccess, showError, showInfo, removeToast],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} onClose={removeToast} />
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

const TYPE_ICON: Record<ToastType, LucideIcon> = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
};

const TYPE_STYLES: Record<ToastType, string> = {
  success: 'border-success bg-success/10 text-success',
  error: 'border-error bg-error/10 text-error',
  info: 'border-primary bg-primary/10 text-primary',
};

/**
 * Renders the live toast stack. Kept inside this module (with plain markup, no
 * `~/components/ui` imports) so the provider has no dependency cycle with the
 * primitives that themselves call `useToast`.
 */
function ToastContainer({
  toasts,
  onClose,
}: {
  toasts: ToastItem[];
  onClose: (id: string) => void;
}) {
  if (toasts.length === 0) {
    return null;
  }

  return (
    <div
      className="fixed bottom-4 right-4 z-50 flex w-[380px] max-w-[calc(100vw-2rem)] flex-col gap-2"
      role="region"
      aria-label="Notifications"
    >
      {toasts.map((toast) => (
        <ToastView key={toast.id} toast={toast} onClose={onClose} />
      ))}
    </div>
  );
}

function ToastView({ toast, onClose }: { toast: ToastItem; onClose: (id: string) => void }) {
  useEffect(() => {
    if (toast.duration === 0) {
      return;
    }
    const timer = setTimeout(() => onClose(toast.id), toast.duration ?? DEFAULT_DURATION);
    return () => clearTimeout(timer);
  }, [toast.id, toast.duration, onClose]);

  const Icon = TYPE_ICON[toast.type];

  return (
    <div
      className={cn(
        'flex items-center gap-3 rounded-lg border px-4 py-3 shadow-lg',
        TYPE_STYLES[toast.type],
      )}
      role="alert"
      aria-live={toast.type === 'error' ? 'assertive' : 'polite'}
    >
      <Icon size={20} aria-hidden="true" />
      <p className="flex-1 text-body">{toast.message}</p>
      <button
        type="button"
        onClick={() => onClose(toast.id)}
        aria-label="Close notification"
        className="text-current opacity-70 hover:opacity-100"
      >
        <X size={16} aria-hidden="true" />
      </button>
    </div>
  );
}
