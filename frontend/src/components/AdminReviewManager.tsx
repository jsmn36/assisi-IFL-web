import { useEffect, useState } from 'react';
import { Check, Edit2, Loader2, MessageSquare, Star, Trash2, X } from 'lucide-react';
import { deleteUpload, getReviews, updateReview, type Review } from '@/lib/storage';
import { useToast } from '@/components/Toast';

function StarPicker({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((s) => (
        <button key={s} type="button" onClick={() => onChange(s)}>
          <Star className={`h-4 w-4 transition-colors ${value >= s ? 'fill-amber-400 text-amber-400' : 'text-slate-600'}`} />
        </button>
      ))}
    </div>
  );
}

export default function AdminReviewManager() {
  const { showToast } = useToast();
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<number | null>(null);
  const [editName, setEditName] = useState('');
  const [editText, setEditText] = useState('');
  const [editRating, setEditRating] = useState(5);
  const [saving, setSaving] = useState(false);

  const load = () => getReviews().then((r) => { setReviews(r); setLoading(false); });
  useEffect(() => { load(); }, []);

  const startEdit = (r: Review) => {
    setEditing(r.id); setEditName(r.name); setEditText(r.text); setEditRating(r.rating);
  };
  const cancelEdit = () => setEditing(null);

  const saveEdit = async (id: number) => {
    if (!editName.trim() || !editText.trim()) return;
    setSaving(true);
    try {
      await updateReview(id, editName.trim(), editText.trim(), editRating);
      showToast('Review updated');
      await load(); setEditing(null);
    } catch { showToast('Failed to update'); } finally { setSaving(false); }
  };

  const remove = async (id: number) => {
    await deleteUpload(id);
    setReviews((r) => r.filter((x) => x.id !== id));
    showToast('Review deleted');
  };

  return (
    <div className="bg-slate-900 border border-white/5 rounded-2xl p-6 shadow-xl shadow-black/20">
      <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-6">
        <MessageSquare className="h-5 w-5 text-emerald-400" /> Student Reviews Manager
        <span className="ml-auto text-xs text-slate-500 font-normal">{reviews.length} review{reviews.length !== 1 ? 's' : ''}</span>
      </h3>

      {loading ? (
        <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin text-emerald-400" /></div>
      ) : reviews.length === 0 ? (
        <p className="text-slate-500 text-sm py-8 text-center">No reviews yet.</p>
      ) : (
        <div className="space-y-3 max-h-[520px] overflow-y-auto pr-1">
          {reviews.map((r) => (
            <div key={r.id} className="bg-slate-950 border border-white/5 rounded-xl p-4">
              {editing === r.id ? (
                <div className="space-y-3">
                  <input
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                    placeholder="Name"
                  />
                  <StarPicker value={editRating} onChange={setEditRating} />
                  <textarea
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    rows={3}
                    className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 resize-none"
                    placeholder="Review text"
                  />
                  <div className="flex gap-2">
                    <button onClick={() => saveEdit(r.id)} disabled={saving} className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition disabled:opacity-50">
                      {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />} Save
                    </button>
                    <button onClick={cancelEdit} className="flex items-center gap-1.5 px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-xs font-bold hover:bg-slate-700 transition">
                      <X className="h-3.5 w-3.5" /> Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-semibold text-white">{r.name}</span>
                      <div className="flex">
                        {[1,2,3,4,5].map((s) => <Star key={s} className={`h-3.5 w-3.5 ${r.rating >= s ? 'fill-amber-400 text-amber-400' : 'text-slate-600'}`} />)}
                      </div>
                      {r.created_at && <span className="text-[11px] text-slate-500 ml-auto">{new Date(r.created_at).toLocaleDateString()}</span>}
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed line-clamp-2">"{r.text}"</p>
                  </div>
                  <div className="flex gap-1.5 shrink-0">
                    <button id={`edit-review-${r.id}`} onClick={() => startEdit(r)} className="p-2 rounded-lg bg-slate-800 hover:bg-blue-500/20 text-slate-400 hover:text-blue-400 transition">
                      <Edit2 className="h-3.5 w-3.5" />
                    </button>
                    <button id={`delete-review-${r.id}`} onClick={() => remove(r.id)} className="p-2 rounded-lg bg-slate-800 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition">
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
