import type { ItemFormErrors } from '~/components/items/ItemForm';
import type { ItemPayload, ItemStatus } from '~/types';

const VALID_STATUSES: readonly ItemStatus[] = ['draft', 'active', 'archived'];

/**
 * Parse and validate the shared item form's `FormData` into a typed
 * {@link ItemPayload}. Returns either a `payload` (valid) or per-field `errors`,
 * so the create/edit actions share one validation path. Client-side `required`
 * attributes are the first line of defense; this is the server-side guard.
 */
export function parseItemForm(
  formData: FormData,
): { payload: ItemPayload; errors?: never } | { payload?: never; errors: ItemFormErrors } {
  const name = (formData.get('name') ?? '').toString().trim();
  const description = (formData.get('description') ?? '').toString().trim();
  const rawStatus = (formData.get('status') ?? '').toString();
  const rawCategory = (formData.get('category') ?? '').toString().trim();

  const errors: ItemFormErrors = {};
  if (!name) {
    errors.name = 'Name is required.';
  }
  const status = VALID_STATUSES.includes(rawStatus as ItemStatus)
    ? (rawStatus as ItemStatus)
    : null;
  if (!status) {
    errors.status = 'Choose a status.';
  }

  if (Object.keys(errors).length > 0 || !status) {
    return { errors };
  }

  return {
    payload: {
      name,
      description,
      status,
      category: rawCategory || null,
    },
  };
}
