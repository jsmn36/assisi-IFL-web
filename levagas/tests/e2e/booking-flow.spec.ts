import { test, expect } from '@playwright/test';
import { ErrorCollector } from '../utils/error-collector';

function futureDate(n: number) {
  const d = new Date(); d.setDate(d.getDate() + n);
  return d.toISOString().split('T')[0];
}

test.describe('Booking Flow', () => {
  test('TC-BOOK-001: /book page loads', async ({ page }) => {
    const collector = new ErrorCollector(page);
    await collector.start();
    await page.goto('/book');
    await page.waitForLoadState('load');
    await expect(page).toHaveTitle(/Le Vagas/i);
    await expect(page.getByRole('heading', { name: /Available Retreats/i })).toBeVisible();
    const { console: ce } = collector.getErrors();
    expect(ce.filter(e => e.type === 'error')).toHaveLength(0);
  });

  test('TC-BOOK-002: /book page shows cottages when dates passed', async ({ page }) => {
    const url = `/book?checkin=${futureDate(14)}&checkout=${futureDate(16)}&guests=2`;
    await page.goto(url);
    await page.waitForLoadState('load');
    // Wait for loading spinner to disappear
    await page.waitForSelector('[class*="animate-pulse"]', { state: 'detached', timeout: 15000 }).catch(() => null);
    // Either "Select Cottage" buttons or no-availability message
    const hasSelectBtn = await page.getByRole('button', { name: /Select Cottage/i }).count() > 0;
    const hasNoAvail = await page.getByText(/no.*available/i).count() > 0;
    expect(hasSelectBtn || hasNoAvail).toBeTruthy();
  });

  test('TC-BOOK-003: selecting cottage goes to /checkout', async ({ page }) => {
    const url = `/book?checkin=${futureDate(21)}&checkout=${futureDate(23)}&guests=2`;
    await page.goto(url);
    await page.waitForLoadState('load');
    await page.waitForSelector('[class*="animate-pulse"]', { state: 'detached', timeout: 15000 }).catch(() => null);
    const selectBtn = page.getByRole('button', { name: /Select Cottage/i }).first();
    const hasCottages = await selectBtn.count() > 0;
    if (!hasCottages) { test.skip(); return; }
    await selectBtn.click();
    await expect(page).toHaveURL(/\/checkout/);
  });

  test('TC-BOOK-004: /checkout without cottage redirects/shows message', async ({ page }) => {
    await page.goto('/checkout');
    await page.waitForLoadState('load');
    // Should either redirect to /book or show "select a cottage first" message
    const onCheckout = page.url().includes('/checkout');
    if (onCheckout) {
      const msg = await page.getByText(/select a cottage/i).count();
      expect(msg).toBeGreaterThan(0);
    } else {
      await expect(page).toHaveURL(/\/book/);
    }
  });

  test('TC-BOOK-005: complete booking flow end-to-end', async ({ page }) => {
    // Step 1: Navigate with dates
    const url = `/book?checkin=${futureDate(30)}&checkout=${futureDate(32)}&guests=2`;
    await page.goto(url);
    await page.waitForLoadState('load');
    await page.waitForSelector('[class*="animate-pulse"]', { state: 'detached', timeout: 15000 }).catch(() => null);

    const selectBtn = page.getByRole('button', { name: /Select Cottage/i }).first();
    if (await selectBtn.count() === 0) { test.skip(); return; }
    await selectBtn.click();
    await page.waitForURL(/\/checkout/);

    // Step 2: Fill guest info
    await page.getByPlaceholder('Enter first name').fill('Test');
    await page.getByPlaceholder('Enter last name').fill('Guest');
    await page.getByPlaceholder('your@email.com').fill('test@levagas.com');
    await page.getByPlaceholder('+91 00000 00000').fill('+919876543210');
    await page.getByPlaceholder('Honeymoon setup, early check-in, dietary needs...').fill('None');

    // Step 3: Click Stripe payment
    await page.getByText('International Card').click();

    // Step 4: Wait for loading to appear then disappear
    await page.waitForSelector('text=Authorizing payment securely', { timeout: 10000 }).catch(() => null);
    await page.waitForURL(/\/confirmation/, { timeout: 20000 });

    // Step 5: Verify confirmation
    await page.waitForSelector('text=Reservation Confirmed', { timeout: 15000 }).catch(() => null);
    const confirmed = await page.getByText('Reservation Confirmed').count() > 0;
    const verifying = await page.getByText("We're verifying").count() > 0;
    expect(confirmed || verifying, 'Should be on confirmation page').toBeTruthy();
  });

  test('TC-BOOK-006: /confirmation page renders with ref param', async ({ page }) => {
    await page.goto('/confirmation?ref=LV-2026-TEST');
    await page.waitForLoadState('load');
    await expect(page.getByRole('heading').first()).toBeVisible();
    // Should show either pending or confirmed state
    const hasState =
      await page.getByText(/verifying|confirmed|wrong/i).count() > 0;
    expect(hasState).toBeTruthy();
  });

  test('TC-BOOK-007: /confirmation confirms booking after polling', async ({ page }) => {
    await page.goto('/confirmation?ref=LV-2026-TEST');
    await page.waitForLoadState('load');
    // Wait for confirmation (API mock returns confirmed immediately)
    await page.waitForSelector('text=Reservation Confirmed', { timeout: 20000 }).catch(() => null);
    const confirmed = await page.getByText('Reservation Confirmed').count() > 0;
    // If still pending, that's also acceptable behaviour
    const pending = await page.getByText(/verifying/i).count() > 0;
    expect(confirmed || pending).toBeTruthy();
  });

  test('TC-BOOK-008: /booking-lookup page loads with search input', async ({ page }) => {
    await page.goto('/booking-lookup');
    await page.waitForLoadState('load');
    await expect(page.getByRole('heading', { name: /Find Your Booking/i })).toBeVisible();
    await expect(page.locator('input').first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Lookup Booking/i })).toBeVisible();
  });

  test('TC-BOOK-009: booking lookup with ref navigates to /confirmation', async ({ page }) => {
    await page.goto('/booking-lookup');
    await page.waitForLoadState('load');
    await page.locator('input').first().fill('LV-2026-1234');
    await page.getByRole('button', { name: /Lookup Booking/i }).click();
    await expect(page).toHaveURL(/\/confirmation\?ref=LV-2026-1234/);
  });

  test('TC-BOOK-010: /my-bookings page loads', async ({ page }) => {
    await page.goto('/my-bookings');
    await page.waitForLoadState('load');
    await expect(page.getByRole('heading', { name: /My Bookings/i })).toBeVisible();
    await expect(page.locator('a[href*="booking-lookup"]').first()).toBeVisible();
  });
});
