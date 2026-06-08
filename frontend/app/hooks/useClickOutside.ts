import { useEffect, type RefObject } from 'react';

/**
 * Calls `handler` when a `mousedown` lands outside the element referenced by
 * `ref`. No-ops while `isEnabled` is false (e.g. a closed popover) and cleans
 * up its document listener on unmount. Used by Modal, Popover and the
 * searchable Select.
 */
export function useClickOutside(
  ref: RefObject<HTMLElement | null>,
  handler: () => void,
  isEnabled: boolean = true,
): void {
  useEffect(() => {
    if (!isEnabled) {
      return;
    }

    const handleClickOutside = (event: MouseEvent): void => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        handler();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [ref, handler, isEnabled]);
}
