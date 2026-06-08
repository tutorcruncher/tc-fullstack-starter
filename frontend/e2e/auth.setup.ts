import { test as setup, expect } from '@playwright/test';
import { config } from 'dotenv';

config({ path: '.env.e2e' });

/**
 * Storage-state file consumed by the `chromium` project (see playwright.config.ts).
 * The login runs once here at the start of the suite; every spec then reuses the
 * saved session instead of logging in per test.
 */
const AUTH_FILE = 'e2e/.auth/user.json';

/**
 * Example login flow. Adapt the request/redirect to your backend:
 *   1. POST credentials to the auth endpoint to obtain a token/session.
 *   2. Hand the token to the app so it persists the session (cookie or storage).
 *   3. Save the resulting browser state to {@link AUTH_FILE}.
 *
 * Guarded so the template is runnable with no backend: when the E2E_* credentials
 * are absent we write an empty storage state (so the dependent `chromium` project
 * can still start) and skip the login rather than hard-failing.
 */
setup('authenticate', async ({ page, context }) => {
  const email = process.env.E2E_EMAIL;
  const password = process.env.E2E_PASSWORD;
  const apiUrl = process.env.E2E_API_URL || 'http://localhost:3000';

  if (!email || !password) {
    await context.storageState({ path: AUTH_FILE });
    setup.skip(true, 'Set E2E_EMAIL and E2E_PASSWORD in .env.e2e to run the authenticated setup.');
    return;
  }

  const response = await page.request.post(`${apiUrl}/auth/login`, {
    data: { email, password },
  });
  expect(response.ok(), `Login failed for ${email}: ${response.status()}`).toBeTruthy();

  const { token } = await response.json();

  await page.goto(`/?token=${token}`);
  await page.waitForLoadState('networkidle');

  await context.storageState({ path: AUTH_FILE });
});
