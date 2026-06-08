# Testing Guide

How tests are written and run in this starter. The goal is a small, self-documenting suite that
exercises the real React Router data flow without a backend, mocks only the API boundary, and
holds the coverage gates. Code conventions are in [`STYLE_GUIDE.md`](./STYLE_GUIDE.md).

## Goals

- **One reason per test.** Each test covers a distinct behavior or branch; its name states what.
  No "just in case" tests, no two tests covering the same thing.
- **Mock only the boundary.** Mock `app/data/api.ts` (the HTTP layer) — never internal business
  logic, hooks, or components under test.
- **Test through the user's eyes.** Query the way a user (and assistive tech) would: by role and
  label, not by implementation detail.
- **Keep tests complete but lean.** Cover every code path (happy, error, loading, empty, each
  branch) with the fewest tests that do so. Share setup via `beforeEach` and the shared helpers.

## Tooling

- **Jest 30 + ts-jest** (config in `jest.config.cjs`), **jsdom** environment.
- **Testing Library** (`@testing-library/react`, `@testing-library/jest-dom`,
  `@testing-library/user-event`) for component/route tests.
- **react-select-event** for driving the `Select` primitive.
- **Playwright** for e2e (`e2e/`, config in `playwright.config.ts`).

```bash
npm test             # run all tests with coverage (CI gate)
npm run test:watch   # watch mode
npm test -- <path>   # a single file
npm run test:e2e     # playwright
```

## Test layout

Tests mirror `app/`:

```
tests/
├── utils/
│   ├── render.tsx       # renderWithRouter / renderWithProviders
│   └── createStub.tsx   # createRouteStub (loader/action route tests)
├── mocks/
│   ├── index.ts         # re-exports all mock data
│   ├── items.ts         # mockItem / mockItems / buildItems factory
│   └── users.ts         # mockUser
├── components/          # component unit tests (mirror app/components)
├── helpers/             # helper-function tests
├── providers/           # provider/context tests
└── routes/              # route loader/action tests
```

## Query priority

Always reach for the most accessible query first. Drop to the next only when the one above can't
express the intent:

1. `getByRole` — accessible roles (`button`, `textbox`, `link`, `dialog`, …) + the `name` option.
2. `getByLabelText` — form fields by their visible label.
3. `getByPlaceholderText` — inputs identified by placeholder.
4. `getByText` — visible text content.
5. `getByTestId` — last resort, with an explicit `data-testid`.

Use `query*` for absence assertions, `find*` for async appearance.

## No snapshots, no comments

- **No snapshot tests.** They assert too much, churn on every change, and document nothing.
  Assert the specific thing the test is about.
- **No comments in test files** (other than nothing — tests should be self-documenting). The
  `describe`/`it` names and the code structure carry the intent. If a test needs a comment to be
  understood, rename it or split it.

## Typed data factories

Build test data from the typed mocks in `tests/mocks/`, never inline ad-hoc objects scattered
across files. A factory takes overrides and returns fully-typed objects:

```ts
import type { Item } from '~/types';

export const mockItem: Item = {
  id: 1,
  name: 'First item',
  description: 'A first item',
  status: 'active',
  category: 'general',
};

export function buildItems(count: number, overrides: Partial<Item> = {}): Item[] {
  return Array.from({ length: count }, (_, i) => ({
    ...mockItem,
    id: i + 1,
    name: `Item ${i + 1}`,
    ...overrides,
  }));
}
```

Re-export everything from `tests/mocks/index.ts` so tests import from one place.

## Render helpers

There is **one** authoritative render path — never call Testing Library's bare `render` with an
ad-hoc router wrapper in individual tests.

- **`renderWithRouter(ui, options?)`** — wraps `ui` in a RR7 router (memory/`createRoutesStub`).
  Use for components that use `<Link>`, `useNavigate`, etc., but no provider context.
- **`renderWithProviders(ui, options?)`** — additionally wraps in `AppProviders` (so `useToast`
  and friends resolve). Use for components that consume cross-cutting context.

```tsx
import { renderWithProviders } from '~/../tests/utils/render';

renderWithProviders(<ItemForm onSubmit={onSubmit} />);
```

## Loader/action route tests — `createRouteStub`

To test a route's **loader/action data flow** in isolation, mock the api layer and drive the route
through `createRouteStub` (a thin wrapper over React Router's `createRoutesStub`). This runs the
real loader/action against the mocked api and renders the route exactly as RR7 would — no backend.

```tsx
import { itemsApi } from '~/data/api';
import { createRouteStub } from '~/../tests/utils/createStub';
import { buildItems } from '~/../tests/mocks';

jest.mock('~/data/api');
const mockItemsApi = jest.mocked(itemsApi);

it('renders the items returned by the loader', async () => {
  mockItemsApi.list.mockResolvedValue({ items: buildItems(3), total: 3, page: 1, page_size: 20 });

  const Stub = createRouteStub([{ path: '/items', Component: ItemsRoute, loader: itemsLoader }]);
  render(<Stub initialEntries={['/items']} />);

  expect(await screen.findByText('Item 1')).toBeInTheDocument();
});
```

Common api-mock shapes:

```ts
mockItemsApi.list.mockResolvedValue({ items, total, page: 1, page_size: 20 }); // success
mockItemsApi.list.mockRejectedValue(new ApiError(500, 'Server error'));        // error → ErrorBoundary
mockItemsApi.create.mockResolvedValue(mockItem);                               // action success → redirect
```

## What to cover

For each component/route/helper, ensure tests cover:

- Happy path (normal render/operation).
- Error states (api rejects → `ErrorBoundary` or form `Alert`).
- Loading/pending UI where applicable.
- Empty states (no rows → empty message).
- Each conditional branch (every `if`/`else`, each variant).
- User interactions (clicks, typing, form submit, sort toggle, pagination).

Group related assertions about a single behavior into one test; keep success vs failure paths,
and behaviors with different setup, separate.

## End-to-end (Playwright)

- **Sequential**: `workers: 1` to avoid login rate limits and per-test re-login.
- **Auth via storage state**: a one-time `e2e/auth.setup.ts` project logs in once and saves the
  storage state; the `chromium` project depends on `setup` and reuses it. Specs import `{ test, expect }`
  from `e2e/fixtures/auth.ts`, which exposes an `authedPage` fixture built on that saved state. Add
  more roles by extending the fixture, not by re-logging-in per test.
- **Server**: started by Playwright in CI (`webServer.command: 'npm run dev'`), reused locally
  (`reuseExistingServer: !process.env.CI`). `baseURL` comes from `E2E_BASE_URL`.
- The example spec (`e2e/items.spec.ts`) walks the full slice: list → New → fill form → submit →
  assert detail → edit → assert update.

## Coverage gates

Committed thresholds (enforced in CI by `npm test`):

| Metric | Threshold |
| --- | --- |
| Statements | 80% |
| Branches | 75% |
| Functions | 70% |
| Lines | 75% |

The framework shell is **excluded** from coverage because it is untestable glue, not logic:
`app/root.tsx`, `app/entry.client.tsx`, `app/routes.ts`, and any `**/+types/**`. If you add a new
piece of pure framework wiring, add it to `coveragePathIgnorePatterns` in `jest.config.cjs` and
note why; everything else must be covered.
