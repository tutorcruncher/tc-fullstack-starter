import type { Route } from './+types/item-edit';
import { useEffect } from 'react';
import { redirect, useActionData, useOutletContext } from 'react-router';
import type { ItemOutletContext } from './item-layout';
import { ApiError, itemsApi } from '~/data/api';
import { ItemForm, type ItemFormErrors } from '~/components/items/ItemForm';
import { useToast } from '~/providers/ToastProvider';
import { buildMetaData } from '~/helpers/meta';
import { parseItemForm } from './item-form-data';

export function meta(): Route.MetaDescriptors {
  return buildMetaData('Edit item');
}

type ActionResult = { errors: ItemFormErrors };

/**
 * Update action. Mirrors the create action but calls `itemsApi.update`. The form
 * is prefilled from the item already loaded by the parent `item-layout` loader
 * (read via `useOutletContext`), so no extra fetch is needed here.
 */
export async function action({
  params,
  request,
}: Route.ActionArgs): Promise<Response | ActionResult> {
  const result = parseItemForm(await request.formData());
  if (result.errors) {
    return { errors: result.errors };
  }

  const id = Number(params.itemId);
  try {
    await itemsApi.update(id, result.payload);
    return redirect(`/items/${id}`);
  } catch (error) {
    if (error instanceof ApiError) {
      return { errors: { form: error.message } };
    }
    throw error;
  }
}

export default function ItemEdit() {
  const { item } = useOutletContext<ItemOutletContext>();
  const actionData = useActionData<ActionResult>();
  const { showError } = useToast();

  useEffect(() => {
    if (actionData?.errors.form) {
      showError(actionData.errors.form);
    }
  }, [actionData, showError]);

  return (
    <main className="container-narrow py-8">
      <ItemForm
        heading={`Edit ${item.name}`}
        submitLabel="Save changes"
        defaultValues={item}
        errors={actionData?.errors}
      />
    </main>
  );
}
