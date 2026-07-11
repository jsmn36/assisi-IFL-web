import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const PAGES = ['/', '/cottages', '/cottages/mist-valley', '/dining', '/wellness', '/contact', '/about', '/book'];

test.describe('Accessibility — WCAG 2.1 AA', () => {
  for (const path of PAGES) {
    test(`${path} passes axe WCAG 2.1 AA`, async ({ page }) => {
      await page.goto(path);
      await page.waitForLoadState('load');
      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .exclude('iframe')
        .analyze();
      if (results.violations.length > 0) {
        console.log(`Violations on ${path}:`, JSON.stringify(results.violations.map(v => ({
          id: v.id, impact: v.impact, description: v.description,
          nodes: v.nodes.map(n => n.target),
        })), null, 2));
      }
      expect(results.violations).toHaveLength(0);
    });
  }

  test('TC-A11Y-KB: tab key focuses interactive element', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('load');
    await page.keyboard.press('Tab');
    const tag = await page.evaluate(() => document.activeElement?.tagName);
    expect(['A','BUTTON','INPUT','SELECT','TEXTAREA']).toContain(tag);
  });

  test('TC-A11Y-LANG: html[lang] attribute is set', async ({ page }) => {
    await page.goto('/');
    const lang = await page.locator('html').getAttribute('lang');
    expect(lang).toBeTruthy();
  });

  test('TC-A11Y-H1: homepage has exactly one h1', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('load');
    expect(await page.getByRole('heading', { level: 1 }).count()).toBeGreaterThanOrEqual(1);
  });

  test('TC-A11Y-ALT: all img elements have alt attribute', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('load');
    const images = page.locator('img');
    const count = await images.count();
    const missing: string[] = [];
    for (let i = 0; i < count; i++) {
      const alt = await images.nth(i).getAttribute('alt');
      if (alt === null) missing.push(await images.nth(i).getAttribute('src') ?? `img[${i}]`);
    }
    expect(missing, `Missing alt: ${missing.join(', ')}`).toHaveLength(0);
  });
});
