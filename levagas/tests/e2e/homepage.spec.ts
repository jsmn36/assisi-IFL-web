import { test, expect } from '@playwright/test';
import { ErrorCollector } from '../utils/error-collector';

test.describe('Homepage', () => {
  let collector: ErrorCollector;

  test.beforeEach(async ({ page }) => {
    collector = new ErrorCollector(page);
    await collector.start();
    await page.goto('/');
    await page.waitForLoadState('load');
  });

  test.afterEach(async () => {
    if (!collector) return;
    const { console: ce, network: ne } = collector.getErrors();
    const jsErrors = ce.filter(e => e.type === 'error');
    const serverErrors = ne.filter(n => n.status >= 500);
    if (jsErrors.length || serverErrors.length) collector.printErrors();
    expect(jsErrors, 'No JS errors expected').toHaveLength(0);
    expect(serverErrors, 'No 5xx errors expected').toHaveLength(0);
  });

  test('TC-HOME-001: page title contains Le Vagas', async ({ page }) => {
    await expect(page).toHaveTitle(/Le Vagas/i);
  });

  test('TC-HOME-002: hero headline is visible', async ({ page }) => {
    // Use heading role to avoid strict mode violation (text also appears in footer/about)
    await expect(page.getByRole('heading', { name: 'Where the Hills Whisper Peace' })).toBeVisible();
  });

  test('TC-HOME-003: tagline Serenity Nature Luxury visible', async ({ page }) => {
    await expect(page.getByText('Serenity • Nature • Luxury').first()).toBeVisible();
  });

  test('TC-HOME-004: booking widget has check-in, check-out, guests and button', async ({ page }) => {
    await expect(page.locator('input[type="date"]').first()).toBeVisible();
    await expect(page.locator('input[type="date"]').nth(1)).toBeVisible();
    await expect(page.locator('select').first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Check Availability/i }).first()).toBeVisible();
  });

  test('TC-HOME-005: booking widget check availability navigates to /book', async ({ page }) => {
    const d1 = new Date(); d1.setDate(d1.getDate() + 7);
    const d2 = new Date(); d2.setDate(d2.getDate() + 9);
    await page.locator('input[type="date"]').first().fill(d1.toISOString().split('T')[0]);
    await page.locator('input[type="date"]').nth(1).fill(d2.toISOString().split('T')[0]);
    await page.locator('select').first().selectOption('2 Guests');
    await page.getByRole('button', { name: /Check Availability/i }).first().click();
    await expect(page).toHaveURL(/\/book/);
  });

  test('TC-HOME-006: featured cottages heading visible', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Luxury Private Cottages' })).toBeVisible();
  });

  test('TC-HOME-007: featured cottages section shows 3 View Details links', async ({ page }) => {
    // FeaturedCottages renders only 3 cottages on the homepage (full 5 are on /cottages)
    const links = page.getByRole('link', { name: /View Details/i });
    const count = await links.count();
    expect(count).toBeGreaterThanOrEqual(3);
  });

  test('TC-HOME-008: View Details link navigates to cottage page', async ({ page }) => {
    await page.getByRole('link', { name: /View Details/i }).first().click();
    await expect(page).toHaveURL(/\/cottages\//);
  });

  test('TC-HOME-009: Explore All 5 Cottages link goes to /cottages', async ({ page }) => {
    const link = page.getByRole('link', { name: /Explore All 5 Cottages/i });
    await expect(link).toBeVisible();
    await link.click();
    await expect(page).toHaveURL('/cottages');
  });

  test('TC-HOME-010: desktop nav links are present and correct', async ({ page }) => {
    const navItems = [
      { text: 'Cottages', href: '/cottages' },
      { text: 'Dining', href: '/dining' },
      { text: 'Wellness', href: '/wellness' },
      { text: 'Experiences', href: '/experiences' },
      { text: 'Gallery', href: '/gallery' },
      { text: 'About', href: '/about' },
      { text: 'Contact', href: '/contact' },
    ];
    for (const item of navItems) {
      const link = page.getByRole('link', { name: item.text }).first();
      await expect(link).toHaveAttribute('href', item.href);
    }
  });

  test('TC-HOME-011: Book Now header link goes to /book', async ({ page }) => {
    // Book Now is a Link wrapping a Button in the desktop header
    const bookNow = page.locator('header').getByRole('link', { name: /Book Now/i }).first();
    await expect(bookNow).toBeVisible();
    await bookNow.click();
    await expect(page).toHaveURL('/book');
  });

  test('TC-HOME-012: LE VAGAS logo links to /', async ({ page }) => {
    await page.goto('/cottages');
    await page.getByRole('link', { name: 'LE VAGAS', exact: true }).click();
    await expect(page).toHaveURL('/');
  });

  test('TC-HOME-013: footer is visible with contact info', async ({ page }) => {
    const footer = page.locator('footer');
    await footer.scrollIntoViewIfNeeded();
    await expect(footer).toBeVisible();
    await expect(footer).toContainText('Vagamon');
    await expect(footer.getByRole('link', { name: /Privacy Policy/i })).toBeVisible();
    await expect(footer.getByRole('link', { name: /Terms/i })).toBeVisible();
    await expect(footer.getByRole('link', { name: /Cancellation/i })).toBeVisible();
  });

  test('TC-HOME-014: all images have non-null src', async ({ page }) => {
    const images = page.locator('img');
    const count = await images.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < count; i++) {
      const src = await images.nth(i).getAttribute('src');
      expect(src, `img[${i}] must have src`).toBeTruthy();
    }
  });

  test('TC-HOME-015: mobile viewport shows hero and hamburger button', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.reload();
    await page.waitForLoadState('load');
    await expect(page.getByRole('heading', { name: 'Where the Hills Whisper Peace' })).toBeVisible();
    // Header hamburger button — only button visible in header at mobile width
    const header = page.locator('header');
    const hamburger = header.locator('button').filter({ has: page.locator('svg') }).last();
    await expect(hamburger).toBeVisible();
  });

  test('TC-HOME-016: mobile menu opens on hamburger click', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.reload();
    await page.waitForLoadState('load');
    const header = page.locator('header');
    await header.locator('button').filter({ has: page.locator('svg') }).last().click();
    await page.waitForTimeout(300);
    // Mobile nav links appear
    await expect(page.getByRole('link', { name: 'Cottages' }).last()).toBeVisible();
  });

  test('TC-HOME-017: SEO meta description present and non-empty', async ({ page }) => {
    const desc = await page.locator('meta[name="description"]').getAttribute('content');
    expect(desc, 'meta description must exist').toBeTruthy();
    expect(desc!.length).toBeGreaterThan(30);
  });

  test('TC-HOME-018: no network 4xx errors on homepage load', async ({ page }) => {
    const { network } = collector.getErrors();
    const client_errors = network.filter(n => n.status >= 400 && n.status < 500);
    expect(client_errors, `4xx errors: ${JSON.stringify(client_errors)}`).toHaveLength(0);
  });
});
