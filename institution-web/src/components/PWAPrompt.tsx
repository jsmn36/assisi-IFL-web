/**
 * PWA Install Prompt
 * Prompt users to install the app
 */
import { useState } from 'react';
import { usePWA } from '@/hooks/usePWA';
import { X, Download } from 'lucide-react';

export function PWAPrompt() {
  const { isInstallable, promptInstall } = usePWA();
  const [dismissed, setDismissed] = useState(false);

  if (!isInstallable || dismissed) {
    return null;
  }

  const handleInstall = async () => {
    const accepted = await promptInstall();
    if (!accepted) {
      setDismissed(true);
    }
  };

  return (
    <div className="fixed bottom-20 left-4 right-4 z-[90] animate-in slide-in-from-bottom-5 duration-300">
      <div className="bg-white rounded-2xl p-5 shadow-2xl border border-blue-50 flex gap-4 items-start">
        <div className="flex-shrink-0 bg-blue-100 p-3 rounded-xl">
          <Download className="h-6 w-6 text-blue-600" />
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-gray-900 mb-1">Install Assisi Social</h3>
          <p className="text-sm text-gray-600 mb-4 leading-relaxed">
            Install our app on your device for quick access, push notifications, and offline capabilities.
          </p>
          
          <div className="flex gap-3">
            <button
              onClick={handleInstall}
              className="flex-1 bg-blue-600 text-white px-5 py-2.5 rounded-xl text-sm font-bold active:bg-blue-700 active:scale-95 transition-all shadow-md"
            >
              Install Now
            </button>
            <button
              onClick={() => setDismissed(true)}
              className="px-5 py-2.5 rounded-xl text-sm font-medium text-gray-500 hover:bg-gray-100 active:bg-gray-200 transition-colors"
            >
              Maybe Later
            </button>
          </div>
        </div>

        <button
          onClick={() => setDismissed(true)}
          className="flex-shrink-0 p-2 hover:bg-gray-100 rounded-full transition-colors active:scale-90"
        >
          <X className="h-5 w-5 text-gray-400" />
        </button>
      </div>
    </div>
  );
}
