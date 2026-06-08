import { test as base, type Page } from '@playwright/test';

/**
 * Authentication fixtures for E2E tests.
 *
 * Uses the storage state saved once by `auth.setup.ts` so login happens a single
 * time per run rather than per test. `authedPage` opens a fresh context with the
 * saved session, giving each test a clean page that is already authenticated.
 *
 * To add more roles, save a second state file in `auth.setup.ts` and add a
 * matching fixture here (e.g. `adminPage` reading `e2e/.auth/admin.json`).
 */
const USER_STATE = 'e2e/.auth/user.json';

export type AuthFixtures = {
  /** A page in a context preloaded with the authenticated storage state. */
  authedPage: Page;
};

export const test = base.extend<AuthFixtures>({
  authedPage: async ({ browser }, use) => {
    const context = await browser.newContext({ storageState: USER_STATE });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },
});

export { expect } from '@playwright/test';
