import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle2, Loader2, MessageSquare, Send, Star } from 'lucide-react';
import { getReviews, saveReview, type Review } from '@/lib/storage';

function Stars({ value, onChange }: { value: number; onChange?: (v: number) => void }) {
  const [hover, setHover] = useState(0);
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((s) => (
        <button
          key={s}
          type="button"
          onClick={() => onChange?.(s)}
          onMouseEnter={() => onChange && setHover(s)}
          onMouseLeave={() => onChange && setHover(0)}
          className={onChange ? 'cursor-pointer' : 'cursor-default'}
        >
          <Star
            className={`h-5 w-5 transition-colors ${(hover || value) >= s ? 'fill-amber-400 text-amber-400' : 'text-slate-300 dark:text-slate-600'}`}
          />
        </button>
      ))}
    </div>
  );
}

function ReviewCard({ review, index }: { review: Review; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(index * 0.07, 0.5) }}
      className="bg-white dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 rounded-2xl p-6 shadow-sm flex flex-col gap-3"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center text-white font-bold text-lg select-none">
            {review.name.trim()[0]?.toUpperCase() || '?'}
          </div>
          <div>
            <p className="font-semibold text-slate-900 dark:text-white text-sm">{review.name}</p>
            <Stars value={review.rating} />
          </div>
        </div>
        {review.created_at && (
          <span className="text-[11px] text-slate-400 shrink-0 mt-1">
            {new Date(review.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
          </span>
        )}
      </div>
      <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed">"{review.text}"</p>
    </motion.div>
  );
}

export default function ReviewSection() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [text, setText] = useState('');
  const [rating, setRating] = useState(5);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => { getReviews().then((r) => { setReviews(r); setLoading(false); }); }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !text.trim()) return;
    setBusy(true);
    try {
      await saveReview(name.trim(), text.trim(), rating);
      const fresh = await getReviews();
      setReviews(fresh);
      setName(''); setText(''); setRating(5); setDone(true);
      setTimeout(() => setDone(false), 4000);
    } catch { /* ignore */ } finally { setBusy(false); }
  };

  const avg = reviews.length ? (reviews.reduce((a, r) => a + r.rating, 0) / reviews.length).toFixed(1) : null;

  return (
    <section id="reviews" className="px-6 py-28 relative bg-gradient-to-b from-slate-50 to-white dark:from-[#0A0D14] dark:to-[#0A0D14] transition-colors duration-300">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[400px] bg-emerald-100/60 dark:bg-emerald-900/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-6xl mx-auto relative z-10">
        {/* Header */}
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white dark:bg-white/5 border border-emerald-200 dark:border-emerald-500/30 text-xs font-semibold text-emerald-700 dark:text-emerald-300 mb-5 shadow-sm">
            <MessageSquare className="h-3.5 w-3.5" /> Student Reviews
          </div>
          <h2 className="text-4xl md:text-5xl font-semibold tracking-tight text-slate-900 dark:text-white mb-3">
            What Our <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 to-teal-400">Students Say</span>
          </h2>
          {avg && (
            <div className="flex items-center justify-center gap-2 mt-3">
              <Stars value={Math.round(Number(avg))} />
              <span className="text-2xl font-bold text-amber-500">{avg}</span>
              <span className="text-sm text-slate-500">({reviews.length} reviews)</span>
            </div>
          )}
        </div>

        <div className="grid lg:grid-cols-3 gap-10">
          {/* Reviews Grid */}
          <div className="lg:col-span-2">
            {loading ? (
              <div className="flex justify-center py-16"><Loader2 className="h-7 w-7 animate-spin text-emerald-500" /></div>
            ) : reviews.length === 0 ? (
              <div className="text-center py-16 text-slate-400">
                <MessageSquare className="h-10 w-10 mx-auto mb-3 opacity-30" />
                <p>No reviews yet. Be the first to share your experience!</p>
              </div>
            ) : (
              <div className="grid sm:grid-cols-2 gap-5">
                {reviews.map((r, i) => <ReviewCard key={r.id} review={r} index={i} />)}
              </div>
            )}
          </div>

          {/* Submit form */}
          <div className="lg:col-span-1">
            <div className="sticky top-28 bg-white dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 rounded-3xl p-7 shadow-lg">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-5 flex items-center gap-2">
                <Star className="h-5 w-5 text-amber-400 fill-amber-400" /> Leave a Review
              </h3>
              <AnimatePresence mode="wait">
                {done ? (
                  <motion.div key="done" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }} className="text-center py-8">
                    <CheckCircle2 className="h-12 w-12 text-emerald-500 mx-auto mb-3" />
                    <p className="font-semibold text-slate-900 dark:text-white">Thank you!</p>
                    <p className="text-sm text-slate-500 mt-1">Your review has been posted.</p>
                  </motion.div>
                ) : (
                  <motion.form key="form" onSubmit={submit} className="space-y-4" initial={{ opacity: 1 }}>
                    <div>
                      <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide block mb-1.5">Your Name *</label>
                      <input
                        id="review-name"
                        required
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="e.g. Jancy Thomas"
                        className="w-full bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl px-4 py-3 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-emerald-500 transition-colors"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide block mb-2">Your Rating *</label>
                      <Stars value={rating} onChange={setRating} />
                    </div>
                    <div>
                      <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide block mb-1.5">Your Review *</label>
                      <textarea
                        id="review-text"
                        required
                        rows={4}
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        placeholder="Share your experience at Assisi IFL..."
                        className="w-full bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl px-4 py-3 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-emerald-500 resize-none transition-colors"
                      />
                    </div>
                    <button
                      id="submit-review"
                      type="submit"
                      disabled={busy}
                      className="w-full py-3.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 text-white font-bold text-sm flex items-center justify-center gap-2 hover:shadow-lg hover:shadow-emerald-500/20 hover:scale-[1.02] transition-all disabled:opacity-60"
                    >
                      {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Send className="h-4 w-4" /> Post Review</>}
                    </button>
                  </motion.form>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
