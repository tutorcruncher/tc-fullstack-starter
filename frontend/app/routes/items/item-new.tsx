import type { Route } from './+types/item-new';
import { useEffect } from 'react';
import { redirect, useActionData } from 'react-router';
import { ApiError, itemsApi } from '~/data/api';
import { ItemForm, type ItemFormErrors } from '~/components/items/ItemForm';
import { useToast } from '~/providers/ToastProvider';
import { buildMetaData } from '~/helpers/meta';
import { parseItemForm } from './item-form-data';

export function meta(): Route.MetaDescriptors {
  return buildMetaData('New item');
}

type ActionResult = { errors: ItemFormErrors };

/**
 * Create action. Validates the submitted form, calls the API client, and
 * redirects to the new item's detail page on success. Validation/server errors
 * are caught and returned to the form (rendered inline + via a toast) rather
 * than bubbling to the `ErrorBoundary`, so the user keeps their input.
 */
export async function action({ request }: Route.ActionArgs): Promise<Response | ActionResult> {
  const result = parseItemForm(await request.formData());
  if (result.errors) {
    return { errors: result.errors };
  }

  try {
    const item = await itemsApi.create(result.payload);
    return redirect(`/items/${item.id}`);
  } catch (error) {
    if (error instanceof ApiError) {
      return { errors: { form: error.message } };
    }
    throw error;
  }
}

export default function ItemNew() {
  const actionData = useActionData<ActionResult>();
  const { showError } = useToast();

  useEffect(() => {
    if (actionData?.errors.form) {
      showError(actionData.errors.form);
    }
  }, [actionData, showError]);

  return (
    <main className="container-narrow py-8">
      <ItemForm heading="New item" submitLabel="Create item" errors={actionData?.errors} />
    </main>
  );
}
