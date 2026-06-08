import { Badge, type Column, Table } from '~/components/ui';
import type { BadgeVariant } from '~/components/ui';
import type { SortState } from '~/hooks/useOrderParams';
import type { Item, ItemStatus } from '~/types';

export interface ItemsTableProps {
  items: Item[];
  sort?: SortState;
  onSortChange?: (sortKey: string) => void;
  total?: number;
  page?: number;
  pageSize?: number;
  onPageChange?: (page: number) => void;
  emptyMessage?: string;
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
 * Column definitions + {@link Table} wiring for the items list. Rows link to the
 * detail route via `getRowHref`. This is the reference for building a typed
 * `Column<T>[]` for a resource.
 */
const COLUMNS: Column<Item>[] = [
  {
    header: 'Name',
    sortKey: 'name',
    cell: (item) => <span className="font-medium text-neutral-900">{item.name}</span>,
  },
  {
    header: 'Description',
    cell: (item) => <span className="line-clamp-1 text-neutral-700">{item.description}</span>,
  },
  {
    header: 'Category',
    cell: (item) => <span className="text-neutral-700">{item.category ?? '—'}</span>,
  },
  {
    header: 'Status',
    sortKey: 'status',
    align: 'right',
    cell: (item) => (
      <Badge variant={STATUS_VARIANTS[item.status]}>{STATUS_LABELS[item.status]}</Badge>
    ),
  },
];

export function ItemsTable({
  items,
  sort,
  onSortChange,
  total,
  page,
  pageSize,
  onPageChange,
  emptyMessage,
}: ItemsTableProps) {
  return (
    <Table
      columns={COLUMNS}
      rows={items}
      getRowKey={(item) => item.id}
      getRowHref={(item) => `/items/${item.id}`}
      sort={sort}
      onSortChange={onSortChange}
      total={total}
      page={page}
      pageSize={pageSize}
      onPageChange={onPageChange}
      emptyMessage={emptyMessage}
    />
  );
}
