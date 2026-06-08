import { clsx, type ClassValue } from 'clsx';

/**
 * The single authoritative class-name helper. Use it everywhere classes are
 * composed conditionally — variant maps, overrides, etc. — instead of manual
 * string concatenation.
 */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}
