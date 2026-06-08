import type { Route } from './+types/items';
import { type FormEvent, useState } from 'react';
import { useNavigation, useSearchParams } from 'react-router';
import { itemsApi } from '~/data/api';
import { Button, Heading, SearchInput } from '~/components/ui';
import { Plus } from '~/components/icons/Icon';
import { ItemsTable } from '~/components/items/ItemsTable';
import { useOrderParams } from '~/hooks/useOrderParams';
import { buildMetaData } from '~/helpers/meta';
import { PAGE_SIZE } from '~/helpers/pagination';
import type { PaginatedResponse } from '~/data/api';
import type { Item, ItemFilters } from '~/types';

export function meta(): Route.MetaDescriptors {
  return buildMetaData('Items');
}

function parseOrderDirection(value: string | null): ItemFilters['order_direction'] {
  if (value === 'asc' || value === 'desc') {
    return value;
  }
  return undefined;
}

/**
 * List loader. List state (page/search/sort) lives entirely in the URL, so the
 * loader is the single source of truth: it reads the search params off the
 * request and calls the API client. `ApiError` bubbles to the root
 * `ErrorBoundary`.
 */
export async function loader({ request }: Route.LoaderArgs): Promise<PaginatedResponse<Item>> {
  const url = new URL(request.url);
  const filters: ItemFilters = {
    page: Number(url.searchParams.get('page')) || 1,
    page_size: PAGE_SIZE.default,
    search: url.searchParams.get('search') ?? undefined,
    order_by: url.searchParams.get('order_by') ?? undefined,
    order_direction: parseOrderDirection(url.searchParams.get('order_direction')),
  };
  return itemsApi.list(filters);
}

export default function Items({ loaderData }: Route.ComponentProps) {
  const { items, total, page, page_size } = loaderData;
  const [searchParams, setSearchParams] = useSearchParams();
  const { sort, toggleSort } = useOrderParams();
  const navigation = useNavigation();
  const [searchTerm, setSearchTerm] = useState(searchParams.get('search') ?? '');

  const isSearching = navigation.state === 'loading';

  const handleSearch = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (searchTerm) {
        next.set('search', searchTerm);
      } else {
        next.delete('search');
      }
      next.delete('page');
      return next;
    });
  };

  const setPage = (next: number): void => {
    setSearchParams((prev) => {
      const params = new URLSearchParams(prev);
      params.set('page', String(next));
      return params;
    });
  };

  return (
    <main className="container-app py-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <Heading level={1} noMargin>
          Items
        </Heading>
        <Button href="/items/new" icon={<Plus size={16} />}>
          New item
        </Button>
      </div>

      <div className="mb-4">
        <SearchInput
          value={searchTerm}
          onChange={setSearchTerm}
          onSubmit={handleSearch}
          placeholder="Search items…"
          loading={isSearching}
        />
      </div>

      <ItemsTable
        items={items}
        sort={sort}
        onSortChange={toggleSort}
        total={total}
        page={page}
        pageSize={page_size}
        onPageChange={setPage}
        emptyMessage={
          searchParams.get('search')
            ? 'No items match your search.'
            : 'No items yet. Create your first one.'
        }
      />
    </main>
  );
}
