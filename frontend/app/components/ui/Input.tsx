import { useId } from 'react';
import type { ChangeEventHandler } from 'react';
import { cn } from '~/helpers/cn';

interface FieldBaseProps {
  label?: string;
  error?: string;
  name?: string;
  id?: string;
  required?: boolean;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export interface InputProps extends FieldBaseProps {
  value: string;
  onChange: ChangeEventHandler<HTMLInputElement>;
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search';
}

export interface TextareaProps extends FieldBaseProps {
  value: string;
  onChange: ChangeEventHandler<HTMLTextAreaElement>;
  rows?: number;
}

const FIELD_CLASSES =
  'w-full rounded-xl border border-neutral-200 bg-white px-3 py-2 text-body outline-none transition focus:border-primary disabled:cursor-not-allowed disabled:bg-neutral-100';
const ERROR_FIELD_CLASSES = 'border-error focus:border-error';

function Label({
  htmlFor,
  children,
  required,
}: {
  htmlFor: string;
  children: string;
  required?: boolean;
}) {
  return (
    <label htmlFor={htmlFor} className="mb-1 block text-small font-medium text-neutral-700">
      {children}
      {required && <span className="ml-0.5 text-error">*</span>}
    </label>
  );
}

function FieldError({ id, message }: { id: string; message: string }) {
  return (
    <p id={id} className="mt-1 text-small text-error">
      {message}
    </p>
  );
}

/** Controlled text input with label, error text and `aria-invalid`/`aria-describedby` wiring. */
export function Input({
  value,
  onChange,
  label,
  error,
  name,
  id,
  type = 'text',
  required,
  disabled,
  placeholder,
  className,
}: InputProps) {
  const generatedId = useId();
  const inputId = id ?? name ?? generatedId;
  const errorId = `${inputId}-error`;

  return (
    <div className={className}>
      {label && (
        <Label htmlFor={inputId} required={required}>
          {label}
        </Label>
      )}
      <input
        id={inputId}
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        required={required}
        disabled={disabled}
        placeholder={placeholder}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={cn(FIELD_CLASSES, error && ERROR_FIELD_CLASSES)}
      />
      {error && <FieldError id={errorId} message={error} />}
    </div>
  );
}

/** Controlled multi-line input mirroring {@link Input}'s label/error a11y wiring. */
export function Textarea({
  value,
  onChange,
  label,
  error,
  name,
  id,
  rows = 4,
  required,
  disabled,
  placeholder,
  className,
}: TextareaProps) {
  const generatedId = useId();
  const inputId = id ?? name ?? generatedId;
  const errorId = `${inputId}-error`;

  return (
    <div className={className}>
      {label && (
        <Label htmlFor={inputId} required={required}>
          {label}
        </Label>
      )}
      <textarea
        id={inputId}
        name={name}
        value={value}
        onChange={onChange}
        rows={rows}
        required={required}
        disabled={disabled}
        placeholder={placeholder}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={cn(FIELD_CLASSES, 'resize-y', error && ERROR_FIELD_CLASSES)}
      />
      {error && <FieldError id={errorId} message={error} />}
    </div>
  );
}
