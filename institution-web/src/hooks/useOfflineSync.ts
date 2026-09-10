/**
 * Hook that watches the online/offline state and drains the offline
 * sync queue when the browser comes back online. Surfaces queue size
 * + flush state for UIs that want to show a banner.
 */
import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { useToast } from '@/components/Toast';
import { flushQueue, getQueueLength, subscribe, type QueuedMutation } from '@/lib/syncQueue';

export interface OfflineSyncState {
  online: boolean;
  pending: number;
  flushing: boolean;
}

export function useOfflineSync(): OfflineSyncState {
  const [online, setOnline] = useState<boolean>(
    typeof navigator !== 'undefined' ? navigator.onLine : true,
  );
  const [pending, setPending] = useState(0);
  const [flushing, setFlushing] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);
    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);
    void getQueueLength().then(setPending);
    const unsub = subscribe((q) => setPending(q.length));
    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
      unsub();
    };
  }, []);

  useEffect(() => {
    if (!online || flushing) return;
    if (pending === 0) return;

    let cancelled = false;
    setFlushing(true);
    void (async () => {
      try {
        const result = await flushQueue(api.client, {
          onConflict: (entry: QueuedMutation) => {
            showToast(
              `Conflict on offline change (${entry.method} ${entry.url}); discarded — please redo manually.`,
              'error',
            );
          },
        });
        if (cancelled) return;
        if (result.succeeded > 0) {
          showToast(`Synced ${result.succeeded} offline change${result.succeeded === 1 ? '' : 's'}.`, 'success');
        }
        if (result.stoppedEarly) {
          showToast('Some offline changes still pending; will retry on reconnect.', 'info' as never);
        }
      } catch (err) {
        if (!cancelled) {
          showToast('Failed to sync offline changes.', 'error');
        }
      } finally {
        if (!cancelled) setFlushing(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [online, pending, flushing, showToast]);

  return { online, pending, flushing };
}
