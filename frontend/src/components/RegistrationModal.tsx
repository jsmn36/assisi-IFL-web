import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle2, ChevronRight, Loader2, Phone, X } from 'lucide-react';
import { useState } from 'react';

const WA_NUMBER = '919961246648';

const BATCHES = [
  'A1 – November 16, 2026',
  'A1 – December 28, 2026',
  'A1 – January 18, 2027',
  'B1/B2 Bridge Course',
  'Online – Flexible',
];

interface FormData {
  name: string;
  phone: string;
  email: string;
  age: string;
  address: string;
  qualification: string;
  batch: string;
  message: string;
}

const EMPTY: FormData = { name: '', phone: '', email: '', age: '', address: '', qualification: '', batch: '', message: '' };

function Field({ label, id, type = 'text', value, onChange, required = true, placeholder = '' }: {
  label: string; id: keyof FormData; type?: string; value: string;
  onChange: (k: keyof FormData, v: string) => void; required?: boolean; placeholder?: string;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
        {label} {required && <span className="text-red-400">*</span>}
      </label>
      <input
        id={id}
        type={type}
        value={value}
        required={required}
        placeholder={placeholder || label}
        onChange={(e) => onChange(id, e.target.value)}
        className="w-full bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl px-4 py-3 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-emerald-500 dark:focus:border-emerald-400 transition-colors"
      />
    </div>
  );
}

function ConfirmModal({ data, onEdit, onConfirm }: { data: FormData; onEdit: () => void; onConfirm: () => void }) {
  const rows: [string, string][] = [
    ['Name', data.name], ['Phone', data.phone], ['Email', data.email],
    ['Age', data.age], ['Address', data.address], ['Qualification', data.qualification],
    ['Batch', data.batch], ...(data.message ? [['Message', data.message] as [string,string]] : []),
  ];
  return (
    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} className="bg-white dark:bg-[#131720] rounded-3xl shadow-2xl p-6 w-full max-w-md mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2.5 bg-emerald-500/10 rounded-xl"><CheckCircle2 className="h-5 w-5 text-emerald-500" /></div>
        <div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white">Confirm Registration</h3>
          <p className="text-xs text-slate-500">Please check your details before submitting.</p>
        </div>
      </div>
      <div className="space-y-2 mb-6">
        {rows.map(([k, v]) => (
          <div key={k} className="flex justify-between text-sm py-2 border-b border-slate-100 dark:border-white/5 last:border-0">
            <span className="text-slate-500 font-medium w-28 shrink-0">{k}</span>
            <span className="text-slate-900 dark:text-white text-right">{v}</span>
          </div>
        ))}
      </div>
      <div className="flex gap-3">
        <button onClick={onEdit} className="flex-1 py-3 rounded-xl border border-slate-200 dark:border-white/10 text-sm font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-white/5 transition">
          Edit
        </button>
        <button
          id="confirm-register"
          onClick={onConfirm}
          className="flex-1 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 text-white text-sm font-bold flex items-center justify-center gap-2 hover:shadow-lg hover:shadow-emerald-500/20 hover:scale-[1.02] transition-all"
        >
          <Phone className="h-4 w-4" /> Send via WhatsApp
        </button>
      </div>
    </motion.div>
  );
}

function SuccessModal({ onClose }: { onClose: () => void }) {
  return (
    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} className="bg-white dark:bg-[#131720] rounded-3xl shadow-2xl p-10 w-full max-w-sm mx-auto text-center">
      <div className="flex justify-center mb-5"><CheckCircle2 className="h-16 w-16 text-emerald-500" /></div>
      <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Registration Sent!</h3>
      <p className="text-slate-500 text-sm mb-6">Your details have been forwarded to our WhatsApp. We'll get back to you shortly.</p>
      <button onClick={onClose} className="w-full py-3 rounded-xl bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-bold text-sm hover:scale-[1.02] transition-all">
        Close
      </button>
    </motion.div>
  );
}

export default function RegistrationModal({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState<FormData>(EMPTY);
  const [step, setStep] = useState<'form' | 'confirm' | 'success'>('form');
  const [busy, setBusy] = useState(false);

  const set = (k: keyof FormData, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setStep('confirm');
  };

  const handleConfirm = () => {
    setBusy(true);
    const msg = [
      '🎓 *New Registration – Assisi IFL*',
      '',
      `👤 *Name:* ${form.name}`,
      `📱 *Phone:* ${form.phone}`,
      `📧 *Email:* ${form.email}`,
      `🎂 *Age:* ${form.age}`,
      `🏠 *Address:* ${form.address}`,
      `📚 *Qualification:* ${form.qualification}`,
      `📅 *Batch:* ${form.batch}`,
      ...(form.message ? [`💬 *Note:* ${form.message}`] : []),
    ].join('\n');
    const url = `https://wa.me/${WA_NUMBER}?text=${encodeURIComponent(msg)}`;
    window.open(url, '_blank');
    setBusy(false);
    setStep('success');
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[200] bg-black/60 dark:bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto"
      onClick={() => step !== 'form' ? undefined : onClose()}
    >
      <div onClick={(e) => e.stopPropagation()} className="w-full max-w-2xl my-6">
        {step === 'form' && (
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} className="bg-white dark:bg-[#131720] rounded-3xl shadow-2xl overflow-hidden">
            {/* Header */}
            <div className="relative bg-gradient-to-r from-emerald-600 to-teal-500 px-8 py-8 text-white">
              <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(circle at 20% 50%, white 1px, transparent 1px), radial-gradient(circle at 80% 20%, white 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
              <button id="register-close" onClick={onClose} className="absolute top-4 right-4 p-2 rounded-full bg-white/20 hover:bg-white/30 transition"><X className="h-4 w-4" /></button>
              <div className="flex items-center gap-3 mb-2">
                <img src="/logo.png" alt="Assisi" className="h-10 w-auto brightness-0 invert opacity-90" />
              </div>
              <h2 className="text-2xl font-bold">Register Now</h2>
              <p className="text-emerald-100 text-sm mt-1">Assisi Institute of Foreign Languages · Bharanaganam</p>
            </div>

            <form onSubmit={handleSubmit} className="p-8 space-y-5">
              <div className="grid sm:grid-cols-2 gap-5">
                <Field label="Full Name" id="name" value={form.name} onChange={set} />
                <Field label="Phone Number" id="phone" type="tel" value={form.phone} onChange={set} placeholder="+91 99612 46648" />
                <Field label="E-mail" id="email" type="email" value={form.email} onChange={set} required={false} />
                <Field label="Age" id="age" type="number" value={form.age} onChange={set} placeholder="e.g. 22" />
              </div>
              <Field label="Address" id="address" value={form.address} onChange={set} placeholder="Your city / district" />
              <div className="grid sm:grid-cols-2 gap-5">
                <Field label="Qualification" id="qualification" value={form.qualification} onChange={set} placeholder="e.g. Plus Two, Graduate" />
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="batch" className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                    Preferred Batch <span className="text-red-400">*</span>
                  </label>
                  <select
                    id="batch"
                    required
                    value={form.batch}
                    onChange={(e) => set('batch', e.target.value)}
                    className="w-full bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl px-4 py-3 text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors"
                  >
                    <option value="" disabled>Select a batch</option>
                    {BATCHES.map((b) => <option key={b} value={b}>{b}</option>)}
                  </select>
                </div>
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="message" className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Additional Message</label>
                <textarea
                  id="message"
                  rows={3}
                  value={form.message}
                  onChange={(e) => set('message', e.target.value)}
                  placeholder="Any questions or special requirements..."
                  className="w-full bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl px-4 py-3 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-emerald-500 resize-none transition-colors"
                />
              </div>

              <button
                id="submit-registration"
                type="submit"
                className="w-full py-4 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-500 text-white font-bold text-base flex items-center justify-center gap-2 hover:shadow-xl hover:shadow-emerald-500/20 hover:scale-[1.01] transition-all"
              >
                {busy ? <Loader2 className="h-5 w-5 animate-spin" /> : <><CheckCircle2 className="h-5 w-5" /> Review & Confirm <ChevronRight className="h-4 w-4" /></>}
              </button>
              <p className="text-center text-xs text-slate-400">Your details will be sent to us via WhatsApp for quick confirmation.</p>
            </form>
          </motion.div>
        )}

        {step === 'confirm' && (
          <ConfirmModal
            data={form}
            onEdit={() => setStep('form')}
            onConfirm={handleConfirm}
          />
        )}

        {step === 'success' && (
          <SuccessModal onClose={onClose} />
        )}
      </div>
    </motion.div>
  );
}
