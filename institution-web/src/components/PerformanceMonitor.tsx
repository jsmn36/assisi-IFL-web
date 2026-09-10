// @ts-nocheck
/**
 * Performance Monitor Component
 * Display performance metrics (dev mode only)
 */
import { useState, useEffect } from 'react';
import { measurePerformance, type PerformanceMetrics } from '@/utils/performance';
import { getDeviceInfo, type DeviceInfo } from '@/utils/mobileDetection';

export function PerformanceMonitor() {
  const [metrics, setMetrics] = useState<Partial<PerformanceMetrics>>({});
  const [deviceInfo, setDeviceInfo] = useState<DeviceInfo | null>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (import.meta.env.MODE !== 'development') {
      return;
    }

    setDeviceInfo(getDeviceInfo());

    setTimeout(() => {
      setMetrics(measurePerformance());
    }, 2000);

    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'P') {
        setIsVisible((v) => !v);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  if (!isVisible || import.meta.env.MODE !== 'development') {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 bg-gray-900 text-white text-xs p-3 rounded-lg shadow-lg z-50 min-w-[200px]">
      <div className="flex justify-between items-center mb-2">
        <span className="font-bold">Performance Monitor</span>
        <button
          onClick={() => setIsVisible(false)}
          className="text-gray-400 hover:text-white"
        >
          ✕
        </button>
      </div>

      {deviceInfo && (
        <div className="mb-2 pb-2 border-b border-gray-700">
          <p>Device: {deviceInfo.screenSize}</p>
          <p>OS: {deviceInfo.isIOS ? 'iOS' : deviceInfo.isAndroid ? 'Android' : 'Desktop'}</p>
          <p>PWA: {deviceInfo.isPWA ? 'Yes' : 'No'}</p>
          <p>Touch: {deviceInfo.hasTouch ? 'Yes' : 'No'}</p>
        </div>
      )}

      <div className="space-y-1">
        {metrics.fcp && (
          <p>FCP: {metrics.fcp.toFixed(0)}ms</p>
        )}
        {metrics.lcp && (
          <p>LCP: {metrics.lcp.toFixed(0)}ms</p>
        )}
        {metrics.ttfb && (
          <p>TTFB: {metrics.ttfb.toFixed(0)}ms</p>
        )}
      </div>

      <p className="mt-2 text-gray-400 text-[10px]">
        Ctrl+Shift+P to toggle
      </p>
    </div>
  );
}
