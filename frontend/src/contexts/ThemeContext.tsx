import React, { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { setCurrencyPreference } from '@/lib/utils';

export type Theme = 'light' | 'dark' | 'system';
export type AccentColor = 'blue' | 'purple' | 'green' | 'orange' | 'rose';
export type FontSize = 'normal' | 'large';

export interface AppearanceSettings {
  theme: Theme;
  accentColor: AccentColor;
  fontSize: FontSize;
  compactSidebar: boolean;
  currency: string;
}

interface ThemeContextValue extends AppearanceSettings {
  setTheme: (t: Theme) => void;
  setAccentColor: (c: AccentColor) => void;
  setFontSize: (s: FontSize) => void;
  setCompactSidebar: (v: boolean) => void;
  setCurrency: (c: string) => void;
}

const ACCENT_PRIMARIES: Record<AccentColor, string> = {
  blue:   '221.2 83.2% 53.3%',
  purple: '262.1 83.3% 57.8%',
  green:  '142.1 76.2% 36.3%',
  orange: '24.6 95% 53.1%',
  rose:   '346.8 77.2% 49.8%',
};

const STORAGE_KEY = 'pms-appearance';

function load(): AppearanceSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return { currency: 'INR', ...JSON.parse(raw) };
  } catch {}
  return { theme: 'light', accentColor: 'blue', fontSize: 'normal', compactSidebar: false, currency: 'INR' };
}

function applySettings(s: AppearanceSettings) {
  const html = document.documentElement;
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const isDark = s.theme === 'dark' || (s.theme === 'system' && prefersDark);
  html.classList.toggle('dark', isDark);
  html.style.setProperty('--primary', ACCENT_PRIMARIES[s.accentColor]);
  html.style.fontSize = s.fontSize === 'large' ? '17px' : '';
  setCurrencyPreference(s.currency);
}

const ThemeContext = createContext<ThemeContextValue>(null!);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<AppearanceSettings>(load);

  useEffect(() => {
    applySettings(settings);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }, [settings]);

  useEffect(() => {
    if (settings.theme !== 'system') return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => applySettings(settings);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [settings]);

  const patch = (p: Partial<AppearanceSettings>) => setSettings(prev => ({ ...prev, ...p }));

  return (
    <ThemeContext.Provider value={{
      ...settings,
      setTheme: t => patch({ theme: t }),
      setAccentColor: c => patch({ accentColor: c }),
      setFontSize: s => patch({ fontSize: s }),
      setCompactSidebar: v => patch({ compactSidebar: v }),
      setCurrency: c => patch({ currency: c }),
    }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);
