import { useId } from 'react';
import ReactSelect from 'react-select';
import type { GroupBase, Props as ReactSelectProps } from 'react-select';
import { cn } from '~/helpers/cn';

export interface SelectProps<Option, IsMulti extends boolean = false> extends ReactSelectProps<
  Option,
  IsMulti,
  GroupBase<Option>
> {
  /** Accessible label rendered above the control and wired to it via `id`. */
  label?: string;
  /** Error text rendered below the control. */
  error?: string;
  /** Mark the field required (visual asterisk + native flag). */
  required?: boolean;
  /** Wrapper className (the control itself is styled internally). */
  className?: string;
}

/**
 * Thin, accessible wrapper around `react-select` applying the project's theme
 * tokens and an associated `<label>`. Used by forms for relation/enum pickers.
 * Generic over the option shape and the multi-select flag.
 */
export function Select<Option, IsMulti extends boolean = false>({
  label,
  error,
  required,
  className,
  inputId,
  ...props
}: SelectProps<Option, IsMulti>) {
  const generatedId = useId();
  const controlId = inputId ?? generatedId;
  const errorId = `${controlId}-error`;

  return (
    <div className={className}>
      {label && (
        <label htmlFor={controlId} className="mb-1 block text-small font-medium text-neutral-700">
          {label}
          {required && <span className="ml-0.5 text-error">*</span>}
        </label>
      )}
      <ReactSelect<Option, IsMulti, GroupBase<Option>>
        inputId={controlId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        classNamePrefix="rr-select"
        unstyled
        classNames={{
          control: ({ isFocused, isDisabled }) =>
            cn(
              'rounded-xl border bg-white px-3 py-1.5 text-body transition',
              isFocused ? 'border-primary' : 'border-neutral-200',
              error && 'border-error',
              isDisabled && 'cursor-not-allowed bg-neutral-100',
            ),
          placeholder: () => 'text-neutral-400',
          menu: () =>
            'mt-1 overflow-hidden rounded-xl border border-neutral-200 bg-white shadow-lg',
          option: ({ isFocused, isSelected }) =>
            cn(
              'cursor-pointer px-3 py-2',
              isSelected
                ? 'bg-primary text-white'
                : isFocused
                  ? 'bg-neutral-50 text-neutral-900'
                  : 'text-neutral-700',
            ),
          multiValue: () => 'mr-1 rounded-md bg-neutral-100 px-1.5 py-0.5',
          indicatorSeparator: () => 'hidden',
        }}
        {...props}
      />
      {error && (
        <p id={errorId} className="mt-1 text-small text-error">
          {error}
        </p>
      )}
    </div>
  );
}
