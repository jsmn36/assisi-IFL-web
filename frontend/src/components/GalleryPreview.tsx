import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Images, Play } from 'lucide-react';
import { getGallery, type GalleryAlbum, type GalleryItem } from '@/lib/storage';
import { ytThumb } from '@/pages/GalleryPage';

function Thumb({ item }: { item: GalleryItem }) {
  const src = item.kind === 'youtube' ? ytThumb(item.youtube_id!) : item.media_url!;
  return (
    <div className="relative overflow-hidden rounded-xl bg-slate-200 dark:bg-white/5 aspect-square">
      {item.kind === 'video' ? (
        <video src={`${src}#t=0.5`} muted playsInline preload="metadata" className="w-full h-full object-cover" />
      ) : (
        <img src={src} alt={item.title} loading="lazy" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" />
      )}
      {item.kind !== 'photo' && (
        <span className="absolute inset-0 flex items-center justify-center">
          <span className={`h-9 w-9 rounded-full flex items-center justify-center ${item.kind === 'youtube' ? 'bg-red-600/90' : 'bg-black/40'}`}>
            <Play className="h-4 w-4 text-white fill-white ml-0.5" />
          </span>
        </span>
      )}
    </div>
  );
}

function AlbumCard({ album, items, title, subtitle, accent }: { album: GalleryAlbum; items: GalleryItem[]; title: React.ReactNode; subtitle: string; accent: string }) {
  const preview = items.slice(0, 4);
  return (
    <Link
      id={`open-${album}`}
      to={`/gallery?album=${album}`}
      className="group relative block p-6 rounded-3xl bg-white dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 shadow-sm hover:shadow-2xl hover:-translate-y-1 transition-all"
    >
      <div className={`absolute -inset-px rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity bg-gradient-to-br ${accent} blur-xl -z-10`} />
      <div className="flex items-start justify-between mb-5">
        <div>
          <h3 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">{title}</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{subtitle}</p>
        </div>
        <span className="p-2 rounded-full bg-slate-100 dark:bg-white/10 group-hover:bg-slate-900 group-hover:text-white dark:group-hover:bg-white dark:group-hover:text-slate-900 transition-colors">
          <ArrowRight className="h-4 w-4" />
        </span>
      </div>
      {preview.length > 0 ? (
        <div className="grid grid-cols-4 gap-2">
          {preview.map((i) => <Thumb key={i.id} item={i} />)}
        </div>
      ) : (
        <div className="h-24 rounded-xl border border-dashed border-slate-300 dark:border-white/10 flex items-center justify-center text-sm text-slate-400 gap-2">
          <Images className="h-4 w-4" /> Coming soon
        </div>
      )}
      <p className="mt-4 text-xs font-semibold uppercase tracking-wider text-slate-400">{items.length} items · Photos, videos & YouTube</p>
    </Link>
  );
}

export default function GalleryPreview() {
  const [items, setItems] = useState<GalleryItem[]>([]);
  useEffect(() => { getGallery().then(setItems); }, []);

  return (
    <motion.div
      id="gallery"
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8 }}
      viewport={{ once: true }}
      className="max-w-7xl mx-auto relative z-10 mt-20 grid md:grid-cols-2 gap-6"
    >
      <AlbumCard
        album="gallery"
        items={items.filter((i) => i.album === 'gallery')}
        title={<>Our <span className="text-emerald-600 dark:text-emerald-400">Gallery</span></>}
        subtitle="Classrooms, events and campus life."
        accent="from-emerald-300/40 to-blue-300/30"
      />
      <AlbumCard
        album="tschuss"
        items={items.filter((i) => i.album === 'tschuss')}
        title={<span className="text-transparent bg-clip-text bg-gradient-to-r from-slate-900 via-red-600 to-amber-500 dark:from-white dark:via-red-500 dark:to-amber-400">Tschüss</span>}
        subtitle="Farewells & students heading to Germany."
        accent="from-red-300/40 to-amber-300/40"
      />
    </motion.div>
  );
}
