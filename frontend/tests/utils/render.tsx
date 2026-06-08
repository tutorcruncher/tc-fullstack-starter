import { type ReactElement } from 'react';
import { render, type RenderOptions, type RenderResult } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { AppProviders } from '~/providers/AppProviders';

export interface RenderWithRouterOptions extends Omit<RenderOptions, 'wrapper'> {
  /** Initial URL the in-memory router starts at. Defaults to `/`. */
  initialPath?: string;
}

/**
 * The one authoritative helper for rendering a component that uses router
 * primitives (`<Link>`, `useNavigate`, `useSearchParams`, …) without a route
 * config. Wraps `ui` in an in-memory router so those primitives resolve. For
 * loader/action route tests use {@link createRouteStub} instead.
 */
export function renderWithRouter(
  ui: ReactElement,
  { initialPath = '/', ...options }: RenderWithRouterOptions = {},
): RenderResult {
  const router = createMemoryRouter([{ path: '*', element: ui }], {
    initialEntries: [initialPath],
  });
  return render(<RouterProvider router={router} />, options);
}

/**
 * Like {@link renderWithRouter}, but additionally wraps `ui` in
 * {@link AppProviders} so context-dependent components (e.g. anything calling
 * `useToast`) work. Use this for component tests by default.
 */
export function renderWithProviders(
  ui: ReactElement,
  { initialPath = '/', ...options }: RenderWithRouterOptions = {},
): RenderResult {
  const router = createMemoryRouter([{ path: '*', element: <AppProviders>{ui}</AppProviders> }], {
    initialEntries: [initialPath],
  });
  return render(<RouterProvider router={router} />, options);
}
