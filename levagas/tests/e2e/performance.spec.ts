import { test, expect } from '@playwright/test';

const PAGES = ['/', '/cottages', '/cottages/mist-valley', '/dining', '/wellness', '/book'];
const MAX_LOAD_MS = 12000;

test.describe('Performance', () => {
  for (const path of PAGES) {
    test(`${path} loads within ${MAX_LOAD_MS / 1000}s`, async ({ page }) => {
      const start = Date.now();
      await page.goto(path);
      await page.waitForLoadState('load');
      const elapsed = Date.now() - start;
      console.log(`  ${path}: ${elapsed}ms`);
      expect(elapsed).toBeLessThan(MAX_LOAD_MS);
    });
  }

  test('TC-PERF-CWV: Core Web Vitals on homepage within thresholds', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const vitals = await page.evaluate(() =>
      new Promise<{ lcp?: number; cls?: number }>((resolve) => {
        const v: { lcp?: number; cls?: number } = {};
        try {
          new PerformanceObserver((l) => {
            const e = l.getEntries().at(-1) as any;
            v.lcp = e?.renderTime || e?.loadTime;
          }).observe({ type: 'largest-contentful-paint', buffered: true });
          new PerformanceObserver((l) => {
            for (const e of l.getEntries() as any[]) {
              if (!e.hadRecentInput) v.cls = (v.cls ?? 0) + e.value;
            }
          }).observe({ type: 'layout-shift', buffered: true });
        } catch {}
        setTimeout(() => resolve(v), 5000);
      })
    );
    console.log('Core Web Vitals:', vitals);
    if (vitals.lcp !== undefined) expect(vitals.lcp).toBeLessThan(5000);
    if (vitals.cls !== undefined) expect(vitals.cls).toBeLessThan(0.25);
  });

  test('TC-PERF-IMAGES: images use web-friendly formats or next/image CDN', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const images = page.locator('img');
    const count = await images.count();
    for (let i = 0; i < count; i++) {
      const src = await images.nth(i).getAttribute('src');
      if (!src || src.startsWith('data:')) continue;
      const ok = src.includes('/_next/image') || src.includes('images.unsplash.com') || /\.(webp|jpg|jpeg|png|svg|avif)(\?|$)/i.test(src);
      expect(ok, `img[${i}] src="${src}" should be a web format or next/image`).toBeTruthy();
    }
  });
});
