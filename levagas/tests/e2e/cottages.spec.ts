import { test, expect } from '@playwright/test';
import { ErrorCollector } from '../utils/error-collector';

const SLUGS = ['mist-valley','emerald-hills','golden-peak','cloud-breeze','celeste-honeymoon-villa'];
const NAMES = ['Mist Valley Cottage','Emerald Hills Cottage','Golden Peak Cottage','Cloud Breeze Cottage','Celeste Honeymoon Villa'];

function futureDate(n: number) {
  const d = new Date(); d.setDate(d.getDate() + n);
  return d.toISOString().split('T')[0];
}

test.describe('Cottages Listing', () => {
  let collector: ErrorCollector;

  test.beforeEach(async ({ page }) => {
    collector = new ErrorCollector(page);
    await collector.start();
    await page.goto('/cottages');
    await page.waitForLoadState('load');
  });

  test.afterEach(async () => {
    if (!collector) return;
    const { console: ce } = collector.getErrors();
    expect(ce.filter(e => e.type === 'error')).toHaveLength(0);
  });

  test('TC-COT-001: page loads with correct heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /Our Luxury Private Cottages/i })).toBeVisible();
  });

  test('TC-COT-002: all 5 cottage names displayed', async ({ page }) => {
    for (const name of NAMES) {
      await expect(page.getByRole('heading', { name }).first()).toBeVisible();
    }
  });

  test('TC-COT-003: sticky availability bar has booking widget', async ({ page }) => {
    await expect(page.locator('input[type="date"]').first()).toBeVisible();
    await expect(page.locator('select').first()).toBeVisible();
    await page.evaluate(() => window.scrollTo(0, 500));
    await page.waitForTimeout(300);
    await expect(page.getByRole('button', { name: /Check Availability/i }).first()).toBeVisible();
  });

  test('TC-COT-004: availability check navigates to /book', async ({ page }) => {
    await page.locator('input[type="date"]').first().fill(futureDate(7));
    await page.locator('input[type="date"]').nth(1).fill(futureDate(9));
    await page.locator('select').first().selectOption('2 Guests');
    await page.getByRole('button', { name: /Check Availability/i }).first().click();
    await expect(page).toHaveURL(/\/book/);
  });

  test('TC-COT-005: View Full Details navigates to a cottage slug page', async ({ page }) => {
    const links = page.getByRole('link', { name: /View Full Details/i });
    await expect(links.first()).toBeVisible();
    await links.first().click();
    const slugPattern = new RegExp(`/cottages/(${SLUGS.join('|')})`);
    await expect(page).toHaveURL(slugPattern);
  });

  test('TC-COT-006: cottage prices show ₹ symbol', async ({ page }) => {
    const prices = await page.getByText(/₹[\d,]+/).all();
    expect(prices.length).toBeGreaterThanOrEqual(5);
  });

  test('TC-COT-007: images have src attributes', async ({ page }) => {
    const images = page.locator('img');
    const count = await images.count();
    for (let i = 0; i < count; i++) {
      const src = await images.nth(i).getAttribute('src');
      expect(src, `img[${i}] must have src`).toBeTruthy();
    }
  });
});

test.describe('Individual Cottage Pages', () => {
  for (const slug of SLUGS) {
    test(`TC-COT-D: /cottages/${slug} loads without errors`, async ({ page }) => {
      const collector = new ErrorCollector(page);
      await collector.start();
      const response = await page.goto(`/cottages/${slug}`);
      await page.waitForLoadState('load');
      expect(response?.status()).toBeLessThan(400);
      await expect(page.getByRole('heading').first()).toBeVisible();
      if (!collector) return;
    const { console: ce } = collector.getErrors();
      expect(ce.filter(e => e.type === 'error')).toHaveLength(0);
    });
  }

  test('TC-COT-D-001: Mist Valley detail page shows correct name', async ({ page }) => {
    await page.goto('/cottages/mist-valley');
    await page.waitForLoadState('load');
    await expect(page.getByRole('heading', { name: 'Mist Valley Cottage', exact: true, level: 1 })).toBeVisible();
  });

  test('TC-COT-D-002: detail page shows price with ₹', async ({ page }) => {
    await page.goto('/cottages/mist-valley');
    await page.waitForLoadState('load');
    await expect(page.getByText(/₹[\d,]+/).first()).toBeVisible();
  });

  test('TC-COT-D-003: detail page check availability goes to /book', async ({ page }) => {
    await page.goto('/cottages/mist-valley');
    await page.waitForLoadState('load');
    await page.locator('input[type="date"]').first().fill(futureDate(7));
    await page.locator('input[type="date"]').nth(1).fill(futureDate(9));
    await page.locator('select').first().selectOption('2 Guests');
    await page.getByRole('button', { name: /Check Availability/i }).first().click();
    await expect(page).toHaveURL(/\/book/);
  });

  test('TC-COT-D-004: detail page has phone and WhatsApp links', async ({ page }) => {
    await page.goto('/cottages/mist-valley');
    await page.waitForLoadState('load');
    const tel = page.locator('a[href^="tel:"]').first();
    const wa = page.locator('a[href*="wa.me"]').first();
    await expect(tel).toBeVisible();
    await expect(wa).toBeVisible();
  });
});
