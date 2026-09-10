// @ts-nocheck
/**
 * Performance Utilities
 * Mobile performance monitoring and optimization
 */

export interface PerformanceMetrics {
  fcp: number;
  lcp: number;
  fid: number;
  cls: number;
  ttfb: number;
}

export function measurePerformance(): Partial<PerformanceMetrics> {
  const metrics: Partial<PerformanceMetrics> = {};

  const fcpEntry = performance.getEntriesByName('first-contentful-paint')[0];
  if (fcpEntry) {
    metrics.fcp = fcpEntry.startTime;
  }

  const navigationEntry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
  if (navigationEntry) {
    metrics.ttfb = navigationEntry.responseStart - navigationEntry.requestStart;
  }

  if ('PerformanceObserver' in window) {
    try {
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1] as any;
        metrics.lcp = lastEntry.renderTime || lastEntry.loadTime;
      });
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
    } catch (e) {
      console.error('LCP observer failed:', e);
    }
  }

  return metrics;
}

export function logPerformance(label: string) {
  if (performance.mark) {
    performance.mark(label);
  }
}

export function measureDuration(startLabel: string, endLabel: string): number {
  if (performance.measure) {
    try {
      performance.measure('duration', startLabel, endLabel);
      const measure = performance.getEntriesByName('duration')[0];
      return measure.duration;
    } catch (e) {
      console.error('Performance measure failed:', e);
      return 0;
    }
  }
  return 0;
}

export function clearPerformanceMarks() {
  if (performance.clearMarks) {
    performance.clearMarks();
  }
  if (performance.clearMeasures) {
    performance.clearMeasures();
  }
}

export function lazyLoadImage(img: HTMLImageElement) {
  const src = img.dataset.src;
  if (!src) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        img.src = src;
        img.classList.add('loaded');
        observer.unobserve(img);
      }
    });
  });

  observer.observe(img);
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout>;
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  return function executedFunction(...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}
