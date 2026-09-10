import { useEffect } from 'react';

type KeyCombo = {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
};

export function useKeyboardShortcut(
  combo: KeyCombo,
  callback: () => void,
  enabled: boolean = true
) {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyPress = (event: KeyboardEvent) => {
      const matchesKey = event.key.toLowerCase() === combo.key.toLowerCase();
      const matchesCtrl = combo.ctrl ? event.ctrlKey || event.metaKey : !event.ctrlKey && !event.metaKey;
      const matchesShift = combo.shift ? event.shiftKey : !event.shiftKey;
      const matchesAlt = combo.alt ? event.altKey : !event.altKey;

      if (matchesKey && matchesCtrl && matchesShift && matchesAlt) {
        event.preventDefault();
        callback();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [combo, callback, enabled]);
}