/**
 * Offline indicator + sync queue status banner.
 *
 * Three states:
 *  - online + no pending: nothing rendered.
 *  - online + flushing/pending: yellow banner with "Syncing N change(s)…".
 *  - offline: red banner with the pending count when present.
 */
import { useOfflineSync } from '@/hooks/useOfflineSync';
import { AlertCircle, RefreshCw, WifiOff } from 'lucide-react';

export function OfflineIndicator() {
  const { online, pending, flushing } = useOfflineSync();

  if (online && pending === 0 && !flushing) {
    return null;
  }

  if (!online) {
    return (
      <div className="fixed top-4 left-4 right-4 z-[200] animate-in slide-in-from-top-4 duration-500">
        <div className="bg-red-600 text-white rounded-2xl p-4 shadow-xl flex items-center justify-between border border-red-500/50 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="bg-red-500 rounded-full p-2">
              <WifiOff className="h-5 w-5 animate-pulse" />
            </div>
            <div>
              <h4 className="font-bold text-sm">Offline</h4>
              <p className="text-xs text-red-100 mt-0.5">
                {pending > 0
                  ? `${pending} change${pending === 1 ? '' : 's'} queued — will sync when you reconnect.`
                  : 'Switching to offline mode'}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="bg-white/15 hover:bg-white/25 px-4 py-2 rounded-xl text-xs font-bold transition-colors active:scale-95 flex items-center gap-1.5"
          >
            <AlertCircle className="h-3.5 w-3.5" />
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Online with pending — flushing or about to.
  return (
    <div className="fixed top-4 left-4 right-4 z-[200] animate-in slide-in-from-top-4 duration-500">
      <div className="bg-amber-500 text-white rounded-2xl p-3 shadow-xl flex items-center gap-3 border border-amber-400/50 backdrop-blur-md">
        <RefreshCw className={`h-4 w-4 ${flushing ? 'animate-spin' : ''}`} />
        <span className="text-sm font-medium">
          {flushing
            ? `Syncing ${pending} offline change${pending === 1 ? '' : 's'}…`
            : `${pending} offline change${pending === 1 ? '' : 's'} pending`}
        </span>
      </div>
    </div>
  );
}
