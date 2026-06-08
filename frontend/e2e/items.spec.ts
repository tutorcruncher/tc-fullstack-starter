import { test, expect } from './fixtures/auth';

/**
 * End-to-end happy path for the example "Items" feature, exercising the full
 * vertical slice the template ships:
 *   list -> New -> fill the form -> create -> detail -> edit -> update.
 *
 * Runs against a live app (a running dev/preview server + a backend serving
 * `/items`), not Jest. It uses the shared auth fixture so it stays consistent
 * with real specs, though the example Items API is unauthenticated.
 */
test.describe('Items feature', () => {
  test('create an item, view it, then edit it', async ({ authedPage: page }) => {
    const name = `E2E item ${Date.now()}`;
    const editedName = `${name} (edited)`;

    await page.goto('/items');
    await expect(page.getByRole('heading', { name: 'Items', level: 1 })).toBeVisible();

    await page.getByRole('link', { name: /new item/i }).click();
    await expect(page).toHaveURL(/\/items\/new$/);
    await expect(page.getByRole('heading', { name: 'New item' })).toBeVisible();

    await page.getByLabel(/name/i).fill(name);
    await page.getByLabel(/description/i).fill('Created by the items e2e spec.');
    await page.getByRole('button', { name: /create item/i }).click();

    await expect(page).toHaveURL(/\/items\/\d+$/);
    await expect(page.getByRole('heading', { name, level: 1 })).toBeVisible();
    await expect(page.getByText('Created by the items e2e spec.')).toBeVisible();

    await page.getByRole('link', { name: /edit/i }).click();
    await expect(page).toHaveURL(/\/items\/\d+\/edit$/);

    const nameField = page.getByLabel(/name/i);
    await nameField.fill(editedName);
    await page.getByRole('button', { name: /save changes/i }).click();

    await expect(page).toHaveURL(/\/items\/\d+$/);
    await expect(page.getByRole('heading', { name: editedName, level: 1 })).toBeVisible();
  });
});
