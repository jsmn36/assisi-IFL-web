/**
 * i18n bootstrap.
 *
 * Three locales scaffolded: en (source of truth), hi, es. Translations
 * live in ./locales/<lang>.json. Detection order: localStorage
 * (`pms_locale`) → browser language → fallback.
 *
 * Usage from any component:
 *
 *   import { useTranslation } from 'react-i18next';
 *   const { t } = useTranslation();
 *   return <button>{t('common.save')}</button>;
 *
 * Switching language is one call: `i18n.changeLanguage('hi')`.
 */
import i18n from 'i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { initReactI18next } from 'react-i18next';

import en from './locales/en.json';
import es from './locales/es.json';
import hi from './locales/hi.json';

export const SUPPORTED_LOCALES = ['en', 'hi', 'es'] as const;
export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number];

void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      hi: { translation: hi },
      es: { translation: es },
    },
    fallbackLng: 'en',
    supportedLngs: SUPPORTED_LOCALES as readonly string[] as string[],
    interpolation: { escapeValue: false }, // React already escapes
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
      lookupLocalStorage: 'pms_locale',
    },
    returnNull: false,
  });

export default i18n;
