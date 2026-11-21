import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { ArrowLeft, Camera, ChevronLeft, ChevronRight, Film, Images, Loader2, Play, Youtube, X } from 'lucide-react';
import { getGallery, type GalleryAlbum, type GalleryItem, type GalleryKind } from '@/lib/storage';

const ALBUMS: { id: GalleryAlbum; label: string; tagline: string }[] = [
  { id: 'gallery', label: 'Gallery', tagline: 'Moments from classrooms, events and campus life.' },
  { id: 'tschuss', label: 'Tschüss', tagline: 'Farewells, send-offs and our students heading to Germany.' },
];

const FILTERS: { id: 'all' | GalleryKind; label: string; icon: typeof Images }[] = [
  { id: 'all', label: 'All', icon: Images },
  { id: 'photo', label: 'Photos', icon: Camera },
  { id: 'video', label: 'Videos', icon: Film },
  { id: 'youtube', label: 'YouTube', icon: Youtube },
];

export const ytThumb = (id: string) => `https://i.ytimg.com/vi/${id}/hqdefault.jpg`;

export function GalleryTile({ item, onClick }: { item: GalleryItem; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="group relative block w-full overflow-hidden rounded-2xl bg-slate-200 dark:bg-white/5 ring-1 ring-black/5 dark:ring-white/10 shadow-sm hover:shadow-xl transition-all break-inside-avoid mb-4"
    >
      {item.kind === 'photo' && (
        <img src={item.media_url!} alt={item.title} loading="lazy" className="w-full h-auto object-cover group-hover:scale-105 transition-transform duration-700" />
      )}
      {item.kind === 'video' && (
        <video src={`${item.media_url}#t=0.5`} muted playsInline preload="metadata" className="w-full h-auto object-cover group-hover:scale-105 transition-transform duration-700" />
      )}
      {item.kind === 'youtube' && (
        <img src={ytThumb(item.youtube_id!)} alt={item.title} loading="lazy" className="w-full aspect-video object-cover group-hover:scale-105 transition-transform duration-700" />
      )}
      <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/0 to-black/0 opacity-80 group-hover:opacity-100 transition-opacity" />
      {item.kind !== 'photo' && (
        <span className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-14 w-14 rounded-full flex items-center justify-center backdrop-blur-md shadow-lg group-hover:scale-110 transition-transform ${item.kind === 'youtube' ? 'bg-red-600/90' : 'bg-white/30'}`}>
          <Play className="h-6 w-6 text-white fill-white ml-0.5" />
        </span>
      )}
      <p className="absolute bottom-3 left-4 right-4 text-left text-sm font-medium text-white truncate">{item.title}</p>
    </button>
  );
}

export function Lightbox({ items, index, onClose, onNav }: { items: GalleryItem[]; index: number; onClose: () => void; onNav: (i: number) => void }) {
  const item = items[index];
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowRight') onNav((index + 1) % items.length);
      if (e.key === 'ArrowLeft') onNav((index - 1 + items.length) % items.length);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [index, items.length, onClose, onNav]);
  if (!item) return null;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-[100] bg-black/90 backdrop-blur-xl flex items-center justify-center p-4" onClick={onClose}>
      <button id="lightbox-close" onClick={onClose} className="absolute top-5 right-5 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white"><X className="h-6 w-6" /></button>
      {items.length > 1 && (
        <>
          <button onClick={(e) => { e.stopPropagation(); onNav((index - 1 + items.length) % items.length); }} className="absolute left-4 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white"><ChevronLeft className="h-6 w-6" /></button>
          <button onClick={(e) => { e.stopPropagation(); onNav((index + 1) % items.length); }} className="absolute right-4 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white"><ChevronRight className="h-6 w-6" /></button>
        </>
      )}
      <motion.div key={item.id} initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="max-w-6xl w-full flex flex-col items-center" onClick={(e) => e.stopPropagation()}>
        {item.kind === 'photo' && <img src={item.media_url!} alt={item.title} className="max-h-[80vh] w-auto rounded-2xl shadow-2xl" />}
        {item.kind === 'video' && <video src={item.media_url!} controls autoPlay playsInline className="max-h-[80vh] w-full rounded-2xl shadow-2xl bg-black" />}
        {item.kind === 'youtube' && (
          <div className="w-full aspect-video rounded-2xl overflow-hidden shadow-2xl">
            <iframe
              className="w-full h-full"
              src={`https://www.youtube-nocookie.com/embed/${item.youtube_id}?autoplay=1&rel=0`}
              title={item.title}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        )}
        <p className="mt-4 text-white/90 text-sm">{item.title} <span className="text-white/40 ml-2">{index + 1} / {items.length}</span></p>
      </motion.div>
    </motion.div>
  );
}

export default function GalleryPage() {
  const [params, setParams] = useSearchParams();
  const album: GalleryAlbum = params.get('album') === 'tschuss' ? 'tschuss' : 'gallery';
  const [filter, setFilter] = useState<'all' | GalleryKind>('all');
  const [items, setItems] = useState<GalleryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState<number | null>(null);

  useEffect(() => {
    document.title = 'Gallery • Assisi Institute of Foreign Languages';
    getGallery().then((g) => { setItems(g); setLoading(false); });
  }, []);

  const visible = useMemo(
    () => items.filter((i) => i.album === album && (filter === 'all' || i.kind === filter)),
    [items, album, filter]
  );
  const current = ALBUMS.find((a) => a.id === album)!;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0A0D14] text-slate-900 dark:text-white font-sans transition-colors">
      <header className="sticky top-0 z-40 bg-white/70 dark:bg-[#0A0D14]/70 backdrop-blur-xl border-b border-slate-200 dark:border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white">
            <ArrowLeft className="h-4 w-4" /> Home
          </Link>
          <div className="flex p-1 rounded-full bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/10">
            {ALBUMS.map((a) => (
              <button
                key={a.id}
                id={`album-${a.id}`}
                onClick={() => { setParams({ album: a.id }); setFilter('all'); }}
                className={`px-5 py-2 rounded-full text-sm font-semibold transition-all ${album === a.id ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900 shadow' : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'}`}
              >
                {a.label}
              </button>
            ))}
          </div>
          <img src="/logo.png" alt="Assisi" className="h-10 w-auto" />
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-14">
        <motion.div key={album} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-10">
          <h1 className="text-5xl md:text-6xl font-semibold tracking-tight mb-4">
            {album === 'tschuss' ? (
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-slate-900 via-red-600 to-amber-500 dark:from-white dark:via-red-500 dark:to-amber-400">Tschüss</span>
            ) : (
              <>Our <span className="text-emerald-600 dark:text-emerald-400">Gallery</span></>
            )}
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-lg font-light">{current.tagline}</p>
        </motion.div>

        <div className="flex flex-wrap justify-center gap-2 mb-10">
          {FILTERS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              id={`filter-${id}`}
              onClick={() => setFilter(id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium border transition-all ${filter === id ? 'bg-emerald-600 border-emerald-600 text-white' : 'bg-white dark:bg-white/5 border-slate-200 dark:border-white/10 text-slate-600 dark:text-slate-300 hover:border-emerald-400'}`}
            >
              <Icon className="h-4 w-4" /> {label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="flex justify-center py-24"><Loader2 className="h-8 w-8 animate-spin text-emerald-500" /></div>
        ) : visible.length === 0 ? (
          <div className="text-center py-24 text-slate-500 dark:text-slate-400">
            <Images className="h-12 w-12 mx-auto mb-4 opacity-40" />
            Nothing here yet. Check back soon!
          </div>
        ) : (
          <div className="columns-1 sm:columns-2 lg:columns-3 gap-4">
            {visible.map((item, i) => (
              <motion.div key={item.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: Math.min(i * 0.04, 0.6) }}>
                <GalleryTile item={item} onClick={() => setOpen(i)} />
              </motion.div>
            ))}
          </div>
        )}
      </main>

      <AnimatePresence>
        {open !== null && <Lightbox items={visible} index={open} onClose={() => setOpen(null)} onNav={setOpen} />}
      </AnimatePresence>
    </div>
  );
}
