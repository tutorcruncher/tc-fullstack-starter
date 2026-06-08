/**
 * Single import surface for the UI primitives:
 *   import { Button, Modal, Table, Heading } from '~/components/ui';
 *
 * Prefer composing these primitives before writing new ones.
 */

export { Button } from './Button';
export type { ButtonProps, ButtonVariant, ButtonSize } from './Button';

export { Input, Textarea } from './Input';
export type { InputProps, TextareaProps } from './Input';

export { Select } from './Select';
export type { SelectProps } from './Select';

export { Modal } from './Modal';
export type { ModalProps, ModalWidth } from './Modal';

export { Table } from './Table';
export type { Column, TableProps } from './Table';

export { Pagination } from './Pagination';
export type { PaginationProps } from './Pagination';

export { Heading } from './Heading';
export type { HeadingProps } from './Heading';

export { Alert } from './Alert';
export type { AlertProps, AlertVariant } from './Alert';

export { Card } from './Card';
export type { CardProps } from './Card';

export { Badge } from './Badge';
export type { BadgeProps, BadgeVariant } from './Badge';

export { SearchInput } from './SearchInput';
export type { SearchInputProps } from './SearchInput';

export { LoadingState } from './LoadingState';
export type { LoadingStateProps } from './LoadingState';

export { ErrorState } from './ErrorState';
export type { ErrorStateProps } from './ErrorState';
