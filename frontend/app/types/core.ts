/**
 * Minimal, stable types shared across the app. Keep this module free of
 * feature-specific shapes — those belong in their own type modules (e.g.
 * `items.ts`). Field casing mirrors the backend by convention.
 */

export interface User {
  id: number;
  name: string;
  email?: string;
}

/**
 * Standard envelope for paginated list endpoints. The `page_size` field is
 * snake_case to mirror a typical JSON backend.
 */
export interface ListApiResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
