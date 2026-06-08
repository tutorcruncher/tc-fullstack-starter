import type { Route } from './+types/item-detail';
import type { ReactNode } from 'react';
import { Form, redirect, useOutletContext } from 'react-router';
import type { ItemOutletContext } from './item-layout';
import { itemsApi } from '~/data/api';
import { Badge, Button, Card, Heading } from '~/components/ui';
import type { BadgeVariant } from '~/components/ui';
import { ArrowLeft, Pencil, Trash } from '~/components/icons/Icon';
import { buildMetaData } from '~/helpers/meta';
import type { ItemStatus } from '~/types';

export function meta(): Route.MetaDescriptors {
  return buildMetaData('Item');
}

const STATUS_LABELS: Record<ItemStatus, string> = {
  draft: 'Draft',
  active: 'Active',
  archived: 'Archived',
};

const STATUS_VARIANTS: Record<ItemStatus, BadgeVariant> = {
  draft: 'neutral',
  active: 'success',
  archived: 'warning',
};

/**
 * Delete action. Mutations go through the API client; on success we redirect
 * back to the list. `ApiError` bubbles to the root `ErrorBoundary`.
 */
export async function action({ params }: Route.ActionArgs): Promise<Response> {
  await itemsApi.remove(Number(params.itemId));
  return redirect('/items');
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-small font-medium text-neutral-500">{label}</dt>
      <dd className="mt-0.5 text-body text-neutral-900">{children}</dd>
    </div>
  );
}

export default function ItemDetail() {
  const { item } = useOutletContext<ItemOutletContext>();

  return (
    <main className="container-narrow py-8">
      <Button href="/items" variant="ghost" size="sm" icon={<ArrowLeft size={16} />}>
        Back to items
      </Button>

      <div className="mt-4 mb-6 flex flex-wrap items-start justify-between gap-3">
        <Heading level={1} noMargin>
          {item.name}
        </Heading>
        <div className="flex items-center gap-2">
          <Button href={`/items/${item.id}/edit`} variant="outline" icon={<Pencil size={16} />}>
            Edit
          </Button>
          <Form method="post">
            <Button type="submit" variant="ghost" icon={<Trash size={16} />}>
              Delete
            </Button>
          </Form>
        </div>
      </div>

      <Card>
        <dl className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <Field label="Status">
            <Badge variant={STATUS_VARIANTS[item.status]}>{STATUS_LABELS[item.status]}</Badge>
          </Field>
          <Field label="Category">{item.category ?? '—'}</Field>
          <div className="sm:col-span-2">
            <Field label="Description">{item.description || '—'}</Field>
          </div>
        </dl>
      </Card>
    </main>
  );
}
