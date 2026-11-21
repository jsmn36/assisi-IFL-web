import { useEffect, useRef, useState } from 'react';
import { Film, Images, Loader2, Trash2, Upload, Youtube } from 'lucide-react';
import { useToast } from '@/components/Toast';
import { deleteUpload, getGallery, parseYouTubeId, saveGalleryItem, type GalleryAlbum, type GalleryItem } from '@/lib/storage';
import { ytThumb } from '@/pages/GalleryPage';

export default function AdminGalleryManager() {
  const { showToast } = useToast();
  const [album, setAlbum] = useState<GalleryAlbum>('gallery');
  const [mode, setMode] = useState<'files' | 'youtube'>('files');
  const [files, setFiles] = useState<File[]>([]);
  const [title, setTitle] = useState('');
  const [ytUrl, setYtUrl] = useState('');
  const [busy, setBusy] = useState(false);
  const [items, setItems] = useState<GalleryItem[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = () => getGallery().then(setItems);
  useEffect(() => { load(); }, []);

  const submit = async () => {
    setBusy(true);
    try {
      if (mode === 'youtube') {
        if (!parseYouTubeId(ytUrl)) throw new Error('Enter a valid YouTube link');
        await saveGalleryItem({ album, title: title || 'YouTube video', youtubeUrl: ytUrl.trim() });
        showToast('YouTube video added');
      } else {
        if (files.length === 0) throw new Error('Select photos or videos');
        for (const f of files) {
          if (f.size > 50 * 1024 * 1024) throw new Error(`${f.name} is over 50MB — use YouTube for long videos`);
          await saveGalleryItem({ album, title: title || f.name.replace(/\.[^.]+$/, ''), file: f });
        }
        showToast(`${files.length} item(s) uploaded`);
      }
      setFiles([]); setTitle(''); setYtUrl('');
      if (fileRef.current) fileRef.current.value = '';
      await load();
    } catch (e: any) {
      showToast(e?.message || 'Upload failed');
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id: number) => {
    await deleteUpload(id);
    setItems((x) => x.filter((i) => i.id !== id));
    showToast('Removed');
  };

  const shown = items.filter((i) => i.album === album);
  const pill = (active: boolean) =>
    `px-4 py-2 rounded-xl text-sm font-bold transition-colors ${active ? 'bg-emerald-600 text-white' : 'bg-slate-950 text-slate-400 hover:text-white border border-white/5'}`;

  return (
    <div className="bg-slate-900 border border-white/5 rounded-2xl p-6 shadow-xl shadow-black/20">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <Images className="h-5 w-5 text-emerald-400" /> Gallery & Tschüss Manager
        </h3>
        <div className="flex gap-2">
          <button id="admin-album-gallery" className={pill(album === 'gallery')} onClick={() => setAlbum('gallery')}>Gallery</button>
          <button id="admin-album-tschuss" className={pill(album === 'tschuss')} onClick={() => setAlbum('tschuss')}>Tschüss</button>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div className="flex gap-2">
            <button className={pill(mode === 'files')} onClick={() => setMode('files')}><Film className="h-4 w-4 inline mr-1" />Photos / Videos</button>
            <button className={pill(mode === 'youtube')} onClick={() => setMode('youtube')}><Youtube className="h-4 w-4 inline mr-1" />YouTube link</button>
          </div>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Title / caption (optional)"
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:border-emerald-500 focus:outline-none"
          />
          {mode === 'files' ? (
            <input
              ref={fileRef}
              type="file"
              multiple
              accept="image/*,video/*"
              onChange={(e) => setFiles(Array.from(e.target.files || []))}
              className="w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:bg-slate-800 file:text-white hover:file:bg-slate-700"
            />
          ) : (
            <input
              value={ytUrl}
              onChange={(e) => setYtUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:border-red-500 focus:outline-none"
            />
          )}
          <button
            id="admin-gallery-upload"
            onClick={submit}
            disabled={busy}
            className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold py-3 rounded-xl transition"
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            Add to {album === 'tschuss' ? 'Tschüss' : 'Gallery'}
          </button>
          <p className="text-xs text-slate-500">Max 50MB per file. For long videos, upload to YouTube and paste the link.</p>
        </div>

        <div className="grid grid-cols-3 gap-2 max-h-80 overflow-y-auto pr-1">
          {shown.length === 0 && <p className="col-span-3 text-sm text-slate-500">No items yet.</p>}
          {shown.map((i) => (
            <div key={i.id} className="relative group aspect-square rounded-lg overflow-hidden bg-slate-950">
              {i.kind === 'video' ? (
                <video src={`${i.media_url}#t=0.5`} muted preload="metadata" className="w-full h-full object-cover" />
              ) : (
                <img src={i.kind === 'youtube' ? ytThumb(i.youtube_id!) : i.media_url!} alt={i.title} className="w-full h-full object-cover" />
              )}
              {i.kind !== 'photo' && (
                <span className="absolute top-1 left-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-black/60 text-white uppercase">{i.kind}</span>
              )}
              <button
                onClick={() => remove(i.id)}
                className="absolute top-1 right-1 p-1.5 rounded-lg bg-rose-600 text-white opacity-0 group-hover:opacity-100 transition"
                title="Delete"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
