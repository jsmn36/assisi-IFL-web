/**
 * Mobile Detection Utilities
 * Detect device types and capabilities
 */

export interface DeviceInfo {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isIOS: boolean;
  isAndroid: boolean;
  isSafari: boolean;
  isChrome: boolean;
  isPWA: boolean;
  hasTouch: boolean;
  screenSize: 'mobile' | 'tablet' | 'desktop';
  orientation: 'portrait' | 'landscape';
}

export function getDeviceInfo(): DeviceInfo {
  const ua = navigator.userAgent;
  const width = window.innerWidth;
  const height = window.innerHeight;

  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(ua);
  const isTablet = /(tablet|ipad|playbook|silk)|(android(?!.*mobi))/i.test(ua);
  const isDesktop = !isMobile && !isTablet;

  const isIOS = /iPad|iPhone|iPod/.test(ua);
  const isAndroid = /Android/.test(ua);

  const isSafari = /^((?!chrome|android).)*safari/i.test(ua);
  const isChrome = /Chrome/.test(ua);

  const isPWA = window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator as any).standalone === true;

  const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

  let screenSize: 'mobile' | 'tablet' | 'desktop' = 'desktop';
  if (width < 768) {
    screenSize = 'mobile';
  } else if (width < 1024) {
    screenSize = 'tablet';
  }

  const orientation = height > width ? 'portrait' : 'landscape';

  return {
    isMobile,
    isTablet,
    isDesktop,
    isIOS,
    isAndroid,
    isSafari,
    isChrome,
    isPWA,
    hasTouch,
    screenSize,
    orientation,
  };
}

export function isMobileDevice(): boolean {
  return getDeviceInfo().isMobile || getDeviceInfo().isTablet;
}

export function getViewportSize() {
  return {
    width: window.innerWidth,
    height: window.innerHeight,
  };
}

export function getDevicePixelRatio(): number {
  return window.devicePixelRatio || 1;
}

export function supportsPassive(): boolean {
  let supportsPassive = false;
  try {
    const opts = Object.defineProperty({}, 'passive', {
      get: function() {
        supportsPassive = true;
      }
    });
    window.addEventListener('testPassive', () => {}, opts);
    window.removeEventListener('testPassive', () => {}, opts);
  } catch (e) {}
  return supportsPassive;
}
