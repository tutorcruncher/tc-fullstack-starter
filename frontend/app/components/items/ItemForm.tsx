import { useState } from 'react';
import { Form, useNavigation } from 'react-router';
import { Alert, Button, Heading, Input, Select, Textarea } from '~/components/ui';
import type { Item, ItemPayload, ItemStatus } from '~/types';

/** Per-field validation errors returned from a create/edit action. */
export type ItemFormErrors = Partial<Record<keyof ItemPayload, string>> & {
  /** Non-field error (e.g. a server failure) shown as a top-level alert. */
  form?: string;
};

export interface ItemFormProps {
  /** Heading + submit-button label (e.g. "Create" / "Save"). */
  heading: string;
  submitLabel: string;
  /** Prefill values when editing. */
  defaultValues?: Partial<Item>;
  /** Field errors returned by the route action. */
  errors?: ItemFormErrors;
}

interface SelectOption<T extends string> {
  value: T;
  label: string;
}

const STATUS_OPTIONS: SelectOption<ItemStatus>[] = [
  { value: 'draft', label: 'Draft' },
  { value: 'active', label: 'Active' },
  { value: 'archived', label: 'Archived' },
];

const CATEGORY_OPTIONS: SelectOption<string>[] = [
  { value: 'general', label: 'General' },
  { value: 'sales', label: 'Sales' },
  { value: 'support', label: 'Support' },
  { value: 'internal', label: 'Internal' },
];

/**
 * Shared create/edit form. Renders controlled `ui` primitives + a `react-select`
 * Select for the category, submitting through a React Router `<Form>` so the
 * route action owns the mutation. Hidden inputs mirror the Select values so they
 * are present in the submitted `FormData`. Used by both `item-new` and
 * `item-edit`.
 */
export function ItemForm({ heading, submitLabel, defaultValues, errors }: ItemFormProps) {
  const navigation = useNavigation();
  const [status, setStatus] = useState<ItemStatus>(defaultValues?.status ?? 'draft');
  const [name, setName] = useState(defaultValues?.name ?? '');
  const [description, setDescription] = useState(defaultValues?.description ?? '');
  const [category, setCategory] = useState<string | null>(defaultValues?.category ?? null);

  const isSubmitting = navigation.state === 'submitting';

  return (
    <Form method="post" className="space-y-5">
      <Heading level={1}>{heading}</Heading>

      {errors?.form && <Alert variant="danger">{errors.form}</Alert>}

      <Input
        name="name"
        label="Name"
        required
        value={name}
        onChange={(event) => setName(event.target.value)}
        error={errors?.name}
      />

      <Textarea
        name="description"
        label="Description"
        value={description}
        onChange={(event) => setDescription(event.target.value)}
        error={errors?.description}
      />

      <Select<SelectOption<ItemStatus>>
        label="Status"
        required
        options={STATUS_OPTIONS}
        value={STATUS_OPTIONS.find((option) => option.value === status) ?? null}
        onChange={(option) => setStatus(option?.value ?? 'draft')}
        error={errors?.status}
      />
      <input type="hidden" name="status" value={status} />

      <Select<SelectOption<string>>
        label="Category"
        isClearable
        placeholder="Select a category…"
        options={CATEGORY_OPTIONS}
        value={CATEGORY_OPTIONS.find((option) => option.value === category) ?? null}
        onChange={(option) => setCategory(option?.value ?? null)}
        error={errors?.category}
      />
      <input type="hidden" name="category" value={category ?? ''} />

      <div className="flex items-center gap-3 pt-2">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : submitLabel}
        </Button>
        <Button href="/items" variant="ghost">
          Cancel
        </Button>
      </div>
    </Form>
  );
}
