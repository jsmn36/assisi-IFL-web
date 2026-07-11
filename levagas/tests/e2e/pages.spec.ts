import { test, expect } from '@playwright/test';
import { ErrorCollector } from '../utils/error-collector';

const PAGES = [
  '/dining',
  '/wellness',
  '/experiences',
  '/gallery',
  '/about',
  '/contact',
  '/cancellation-policy',
  '/privacy-policy',
  '/terms-conditions',
];

test.describe('Content Pages — Smoke', () => {
  for (const path of PAGES) {
    test(`${path} loads without errors`, async ({ page }) => {
      const collector = new ErrorCollector(page);
      await collector.start();
      const response = await page.goto(path);
      await page.waitForLoadState('load');
      expect(response?.status(), `${path} must not 4xx/5xx`).toBeLessThan(400);
      await expect(page.getByRole('heading').first()).toBeVisible();
      const { console: ce, network: ne } = collector.getErrors();
      expect(ce.filter(e => e.type === 'error'), `${path} JS errors`).toHaveLength(0);
      expect(ne.filter(n => n.status >= 500), `${path} 5xx errors`).toHaveLength(0);
    });
  }

  test('dining: shows dining heading and images', async ({ page }) => {
    await page.goto('/dining');
    await page.waitForLoadState('load');
    await expect(page.getByRole('heading').first()).toBeVisible();
    expect(await page.locator('img').count()).toBeGreaterThan(0);
  });

  test('gallery: shows 8 images with alt text', async ({ page }) => {
    await page.goto('/gallery');
    await page.waitForLoadState('load');
    await expect(page.getByRole('heading', { name: 'Gallery' })).toBeVisible();
    const images = page.locator('img');
    const count = await images.count();
    expect(count).toBeGreaterThanOrEqual(8);
    for (let i = 0; i < count; i++) {
      const alt = await images.nth(i).getAttribute('alt');
      expect(alt, `Gallery img[${i}] must have alt`).not.toBeNull();
    }
  });

  test('contact: shows phone number and email', async ({ page }) => {
    await page.goto('/contact');
    await page.waitForLoadState('load');
    await expect(page.getByText('+91 98765 43210').first()).toBeVisible();
    await expect(page.getByText('info@levagas.com').first()).toBeVisible();
  });

  test('contact: form submission shows success message', async ({ page }) => {
    await page.goto('/contact');
    await page.waitForLoadState('load');
    await page.getByPlaceholder('Your name').fill('Test User');
    await page.getByPlaceholder('your@email.com').fill('test@levagas.com');
    await page.getByPlaceholder('Tell us about your plans...').fill('Test message');
    await page.getByRole('button', { name: /Send Enquiry/i }).click();
    await expect(page.getByText(/Message Received/i)).toBeVisible();
  });

  test('about: mentions Le Vagas and Vagamon', async ({ page }) => {
    await page.goto('/about');
    await page.waitForLoadState('load');
    const hasContext =
      (await page.getByText(/Le Vagas/i).count()) > 0 ||
      (await page.getByText(/Vagamon/i).count()) > 0;
    expect(hasContext).toBeTruthy();
  });

  test('wellness: shows wellness/spa content', async ({ page }) => {
    await page.goto('/wellness');
    await page.waitForLoadState('load');
    await expect(page.getByRole('heading').first()).toBeVisible();
  });

  test('experiences: shows experiences content', async ({ page }) => {
    await page.goto('/experiences');
    await page.waitForLoadState('load');
    await expect(page.getByRole('heading').first()).toBeVisible();
  });

  test('cancellation-policy: page renders legal content', async ({ page }) => {
    await page.goto('/cancellation-policy');
    await page.waitForLoadState('load');
    await expect(page.getByRole('heading').first()).toBeVisible();
  });

  test('privacy-policy: page renders legal content', async ({ page }) => {
    await page.goto('/privacy-policy');
    await page.waitForLoadState('load');
    await expect(page.getByRole('heading').first()).toBeVisible();
  });

  test('terms-conditions: page renders legal content', async ({ page }) => {
    await page.goto('/terms-conditions');
    await page.waitForLoadState('load');
    await expect(page.getByRole('heading').first()).toBeVisible();
  });
});
