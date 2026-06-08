import { apiBaseUrl } from '~/helpers/env';
import { safeGetItem } from '~/helpers/storage';
import type { Item, ItemFilters, ItemPayload, User } from '~/types';

export { apiBaseUrl };

/** Error thrown by {@link apiRequest} when the response status is not ok. */
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/** Standard list response shape (snake_case `page_size` mirrors the backend). */
export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

/**
 * The single typed HTTP client. Injects the base URL and JSON headers, attaches
 * a bearer token from storage when present, parses the JSON body, and throws
 * {@link ApiError} on a non-ok response (message from `detail` or `error`).
 *
 * Components never call `fetch()` directly — loaders and actions call this (or a
 * resource object built on it, like {@link itemsApi}).
 */
export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = safeGetItem('token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers ?? {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const response = await fetch(`${apiBaseUrl}${path}`, { ...options, headers });
  const body = await response.json().catch(() => null);

  if (!response.ok) {
    const message = body?.detail ?? body?.error ?? response.statusText ?? 'Request failed';
    throw new ApiError(response.status, message);
  }

  return body as T;
}

type QueryValue = string | number | boolean | null | undefined;

/** Build a query string from a flat filter object, skipping empty values. */
function withQuery(path: string, params?: object): string {
  if (!params) {
    return path;
  }
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params as Record<string, QueryValue>)) {
    if (value === undefined || value === null || value === '') {
      continue;
    }
    search.append(key, String(value));
  }
  const qs = search.toString();
  return qs ? `${path}?${qs}` : path;
}

/**
 * Example resource client. Group each resource's endpoints into an object like
 * this, all routed through {@link apiRequest}, and call them from loaders and
 * actions.
 */
export const itemsApi = {
  list: (params?: ItemFilters): Promise<PaginatedResponse<Item>> =>
    apiRequest(withQuery('/items', params)),

  get: (id: number): Promise<Item> => apiRequest(`/items/${id}`),

  create: (payload: ItemPayload): Promise<Item> =>
    apiRequest('/items', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  update: (id: number, payload: ItemPayload): Promise<Item> =>
    apiRequest(`/items/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),

  remove: (id: number): Promise<void> =>
    apiRequest(`/items/${id}`, {
      method: 'DELETE',
    }),
};

/**
 * Auth resource client. `checkUser` validates the stored bearer token by
 * fetching the signed-in user; it rejects (with {@link ApiError}) when the
 * token is missing or invalid. Consumed by `AuthProvider`.
 */
export const authApi = {
  checkUser: (): Promise<User> => apiRequest('/users/me'),
};
