/**
 * Language switcher.
 *
 * Compact dropdown that updates i18next + persists the choice. The
 * detector picks up the persisted value on next boot.
 */
import { useTranslation } from 'react-i18next';
import { Globe } from 'lucide-react';

const LABELS: Record<string, string> = {
  en: 'English',
  hi: 'हिन्दी',
  es: 'Español',
};

export function LanguageSwitcher({ className = '' }: { className?: string }) {
  const { i18n } = useTranslation();
  const current = (i18n.resolvedLanguage ?? i18n.language ?? 'en').split('-')[0];

  const onChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    void i18n.changeLanguage(e.target.value);
  };

  return (
    <label className={`inline-flex items-center gap-2 text-sm ${className}`}>
      <Globe className="h-4 w-4 text-gray-500" aria-hidden />
      <span className="sr-only">Language</span>
      <select
        value={current}
        onChange={onChange}
        className="bg-transparent border-0 text-sm font-medium text-gray-700 focus:outline-none focus:ring-0 cursor-pointer"
      >
        {Object.entries(LABELS).map(([code, label]) => (
          <option key={code} value={code}>
            {label}
          </option>
        ))}
      </select>
    </label>
  );
}
