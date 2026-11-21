import { useEffect, useState } from 'react';
import { Bell, BellRing, Loader2 } from 'lucide-react';
import { disablePush, enablePush, isPushEnabled, pushSupported } from '@/lib/push';

export default function NotifyButton() {
  const [enabled, setEnabled] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    isPushEnabled().then(setEnabled).catch(() => {});
  }, []);

  useEffect(() => {
    if (!msg) return;
    const t = setTimeout(() => setMsg(null), 3500);
    return () => clearTimeout(t);
  }, [msg]);

  if (!pushSupported()) return null;

  const toggle = async () => {
    setBusy(true);
    try {
      if (enabled) {
        await disablePush();
        setEnabled(false);
        setMsg('Notifications turned off');
      } else {
        const ok = await enablePush();
        setEnabled(ok);
        setMsg(ok ? "You'll be notified about new updates 🎉" : 'Permission was blocked in your browser');
      }
    } catch (e: any) {
      setMsg(e?.message || 'Something went wrong');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="relative">
      <button
        id="notify-toggle"
        onClick={toggle}
        disabled={busy}
        title={enabled ? 'Turn off notifications' : 'Get notified about new updates'}
        className={`relative p-2 rounded-full border transition-all ${
          enabled
            ? 'bg-blue-600 text-white border-blue-600 hover:bg-blue-500'
            : 'bg-slate-100 dark:bg-white/10 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-white/10 hover:bg-slate-200 dark:hover:bg-white/20'
        }`}
      >
        {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : enabled ? <BellRing className="h-4 w-4" /> : <Bell className="h-4 w-4" />}
        {!enabled && !busy && (
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
        )}
      </button>
      {msg && (
        <div className="absolute right-0 top-12 w-60 text-xs bg-slate-900 text-white dark:bg-white dark:text-slate-900 px-3 py-2 rounded-xl shadow-xl">
          {msg}
        </div>
      )}
    </div>
  );
}
