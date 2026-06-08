/**
 * Types for the example "Items" feature. Replace this module (or add your own
 * resource modules alongside it) when adapting the starter to your domain, then
 * re-export from `types/index.ts`.
 */

export type ItemStatus = 'draft' | 'active' | 'archived';

export interface Item {
  id: number;
  name: string;
  description: string;
  status: ItemStatus;
  category?: string | null;
}

/**
 * The write shape sent to create/update endpoints. Omits server-managed fields
 * (e.g. `id`).
 */
export interface ItemPayload {
  name: string;
  description: string;
  status: ItemStatus;
  category?: string | null;
}

/**
 * Query parameters accepted by the list endpoint. Drives the URL-backed list
 * state (page/search/sort) on the items list route.
 */
export interface ItemFilters {
  page?: number;
  page_size?: number;
  search?: string;
  status?: ItemStatus;
  order_by?: string;
  order_direction?: 'asc' | 'desc';
}
