// Web Push helpers – subscriptions are stored on the Render backend.
const API_BASE = 'https://assisi-ifl-web-1.onrender.com';

export const pushSupported = () =>
  typeof window !== 'undefined' &&
  'serviceWorker' in navigator &&
  'PushManager' in window &&
  'Notification' in window;

function urlBase64ToUint8Array(base64: string): Uint8Array {
  const padding = '='.repeat((4 - (base64.length % 4)) % 4);
  const raw = atob((base64 + padding).replace(/-/g, '+').replace(/_/g, '/'));
  return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)));
}

async function getRegistration() {
  return (await navigator.serviceWorker.getRegistration('/sw.js')) ?? navigator.serviceWorker.register('/sw.js');
}

export async function isPushEnabled(): Promise<boolean> {
  if (!pushSupported() || Notification.permission !== 'granted') return false;
  const reg = await navigator.serviceWorker.getRegistration('/sw.js');
  return !!(reg && (await reg.pushManager.getSubscription()));
}

export async function enablePush(): Promise<boolean> {
  if (!pushSupported()) throw new Error('Notifications are not supported on this browser.');
  const permission = await Notification.requestPermission();
  if (permission !== 'granted') return false;

  const reg = await getRegistration();
  await navigator.serviceWorker.ready;
  const res = await fetch(`${API_BASE}/push/public-key`);
  if (!res.ok) throw new Error('Notifications are not configured on the server yet.');
  const { publicKey } = await res.json();

  const sub =
    (await reg.pushManager.getSubscription()) ??
    (await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(publicKey) as BufferSource,
    }));

  await fetch(`${API_BASE}/push/subscribe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(sub.toJSON()),
  });
  return true;
}

export async function disablePush(): Promise<void> {
  const reg = await navigator.serviceWorker.getRegistration('/sw.js');
  const sub = await reg?.pushManager.getSubscription();
  if (!sub) return;
  await fetch(`${API_BASE}/push/unsubscribe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ endpoint: sub.endpoint }),
  }).catch(() => {});
  await sub.unsubscribe();
}
