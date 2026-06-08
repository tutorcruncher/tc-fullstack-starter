import { render, type RenderResult } from '@testing-library/react';
import { createRoutesStub } from 'react-router';
import { AppProviders } from '~/providers/AppProviders';

type StubRoutes = Parameters<typeof createRoutesStub>[0];

/**
 * Loosely-typed stub route. `loader`/`action` are `unknown` so the type-narrowed
 * framework loaders generated from `routes.ts` (`Route.LoaderArgs` with specific
 * params) can be passed straight in without per-test casts.
 */
export interface StubRoute {
  path?: string;
  index?: boolean;
  Component?: unknown;
  loader?: unknown;
  action?: unknown;
  children?: StubRoute[];
}

export interface CreateRouteStubOptions {
  /** URL the stub router starts at. Defaults to `/`. */
  initialPath?: string;
  /** Wrap the routes in {@link AppProviders} (Toast, …). Defaults to true. */
  withProviders?: boolean;
}

/**
 * Wrapper over React Router's `createRoutesStub` for testing routes that use
 * loaders/actions in isolation. Pass the same route objects you would register
 * in `routes.ts` (with `loader`/`action`/`Component`), mock the `~/data/api`
 * layer, and assert on the loader-fed render or action result.
 */
export function createRouteStub(
  routes: StubRoute[],
  { initialPath = '/', withProviders = true }: CreateRouteStubOptions = {},
): RenderResult {
  const Stub = createRoutesStub(routes as unknown as StubRoutes);
  const element = <Stub initialEntries={[initialPath]} />;
  return render(withProviders ? <AppProviders>{element}</AppProviders> : element);
}
