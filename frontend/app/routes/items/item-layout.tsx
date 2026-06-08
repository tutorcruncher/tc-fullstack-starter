import type { Route } from './+types/item-layout';
import { Outlet } from 'react-router';
import { itemsApi } from '~/data/api';
import type { Item } from '~/types';

/** Context shape exposed to the detail/edit children via `<Outlet context>`. */
export type ItemOutletContext = { item: Item };

/**
 * Parent layout for a single item. Loads the record once and shares it with the
 * detail and edit children through `<Outlet context>`, so neither child re-fetches
 * it. `ApiError` (e.g. a 404 for a missing/cross-resource id) bubbles to the root
 * `ErrorBoundary`.
 */
export async function loader({ params }: Route.LoaderArgs): Promise<{ item: Item }> {
  const item = await itemsApi.get(Number(params.itemId));
  return { item };
}

export default function ItemLayout({ loaderData }: Route.ComponentProps) {
  return <Outlet context={{ item: loaderData.item } satisfies ItemOutletContext} />;
}
