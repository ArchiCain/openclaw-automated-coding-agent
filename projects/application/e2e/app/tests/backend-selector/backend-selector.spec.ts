import { test, expect } from '@playwright/test';
import { testUser, paths, timeouts } from '../../fixtures/test-data';

/**
 * Backend Selector E2E Tests
 *
 * Prerequisites:
 * - All services running: task start-local
 * - User authenticated (tests handle login in beforeEach)
 *
 * Test Coverage:
 * - Backend selector toggle is visible in the app header
 * - Default selection is "NestJS"
 * - Switching to "FastAPI" persists to localStorage (preferred-backend=fastapi)
 * - Page reload retains "FastAPI" selection
 * - Switching back to "NestJS" updates localStorage
 *
 * Note: These tests focus on UI state and localStorage persistence.
 * Actual API routing is covered by backend integration tests.
 */

const STORAGE_KEY = 'preferred-backend';

/**
 * Helper: log in as admin user.
 */
async function login(page: import('@playwright/test').Page): Promise<void> {
  await page.goto(paths.login);
  await page.getByLabel(/username/i).fill(testUser.username);
  await page.getByLabel(/password/i).fill(testUser.password);
  await page.getByRole('button', { name: /sign in/i }).click();
  await page.waitForURL((url: URL) => !url.pathname.includes('/login'), {
    timeout: timeouts.medium,
  });
}

test.describe('Backend Selector', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage so each test starts with a clean state
    await page.goto('/');
    await page.evaluate((key: string) => localStorage.removeItem(key), STORAGE_KEY);

    // Log in and land on the home page
    await login(page);
    await page.goto(paths.home);
  });

  test.afterEach(async ({ page }) => {
    // Clean up: remove the stored preference to avoid cross-test leakage
    await page.evaluate((key: string) => localStorage.removeItem(key), STORAGE_KEY);
  });

  test('shows backend selector toggle in the header', async ({ page }) => {
    // The toggle group should be present in the toolbar
    const toggleGroup = page.getByRole('group', { name: /select backend/i });
    await expect(toggleGroup).toBeVisible({ timeout: timeouts.short });

    // Both options should be rendered
    await expect(page.getByRole('radio', { name: /nestjs/i })).toBeVisible();
    await expect(page.getByRole('radio', { name: /fastapi/i })).toBeVisible();
  });

  test('defaults to NestJS when no preference is stored', async ({ page }) => {
    // NestJS toggle should be the selected one by default
    const nestjsToggle = page.getByRole('radio', { name: /nestjs/i });
    await expect(nestjsToggle).toBeVisible({ timeout: timeouts.short });
    await expect(nestjsToggle).toHaveAttribute('aria-checked', 'true');

    // FastAPI should NOT be selected
    const fastapiToggle = page.getByRole('radio', { name: /fastapi/i });
    await expect(fastapiToggle).toHaveAttribute('aria-checked', 'false');

    // localStorage should not have a value (or should be nestjs)
    const stored = await page.evaluate((key: string) => localStorage.getItem(key), STORAGE_KEY);
    expect(stored === null || stored === 'nestjs').toBeTruthy();
  });

  test('switches to FastAPI and persists to localStorage', async ({ page }) => {
    // Click the FastAPI toggle
    const fastapiToggle = page.getByRole('radio', { name: /fastapi/i });
    await fastapiToggle.click();

    // FastAPI should now be selected
    await expect(fastapiToggle).toHaveAttribute('aria-checked', 'true', { timeout: timeouts.short });

    // NestJS should be deselected
    const nestjsToggle = page.getByRole('radio', { name: /nestjs/i });
    await expect(nestjsToggle).toHaveAttribute('aria-checked', 'false');

    // localStorage should reflect the change
    const stored = await page.evaluate((key: string) => localStorage.getItem(key), STORAGE_KEY);
    expect(stored).toBe('fastapi');
  });

  test('retains FastAPI selection after page reload', async ({ page }) => {
    // Switch to FastAPI first
    const fastapiToggle = page.getByRole('radio', { name: /fastapi/i });
    await fastapiToggle.click();
    await expect(fastapiToggle).toHaveAttribute('aria-checked', 'true', { timeout: timeouts.short });

    // Reload the page
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForURL((url: URL) => !url.pathname.includes('/login'), {
      timeout: timeouts.medium,
    });
    await page.goto(paths.home);

    // FastAPI should still be selected after reload
    const fastapiToggleAfterReload = page.getByRole('radio', { name: /fastapi/i });
    await expect(fastapiToggleAfterReload).toBeVisible({ timeout: timeouts.short });
    await expect(fastapiToggleAfterReload).toHaveAttribute('aria-checked', 'true');

    // Verify localStorage is still set
    const stored = await page.evaluate((key: string) => localStorage.getItem(key), STORAGE_KEY);
    expect(stored).toBe('fastapi');
  });

  test('switches back to NestJS and updates localStorage', async ({ page }) => {
    // First set FastAPI as the preference via localStorage directly
    await page.evaluate(
      ({ key, value }: { key: string; value: string }) => localStorage.setItem(key, value),
      { key: STORAGE_KEY, value: 'fastapi' }
    );

    // Reload to pick up the stored preference
    await page.goto(paths.home);

    // FastAPI should be active
    const fastapiToggle = page.getByRole('radio', { name: /fastapi/i });
    await expect(fastapiToggle).toHaveAttribute('aria-checked', 'true', { timeout: timeouts.short });

    // Now switch back to NestJS
    const nestjsToggle = page.getByRole('radio', { name: /nestjs/i });
    await nestjsToggle.click();

    // NestJS should now be selected
    await expect(nestjsToggle).toHaveAttribute('aria-checked', 'true', { timeout: timeouts.short });
    await expect(fastapiToggle).toHaveAttribute('aria-checked', 'false');

    // localStorage should be updated to nestjs
    const stored = await page.evaluate((key: string) => localStorage.getItem(key), STORAGE_KEY);
    expect(stored).toBe('nestjs');
  });
});
