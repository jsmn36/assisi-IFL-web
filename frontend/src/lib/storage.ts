/* eslint-disable @typescript-eslint/no-explicit-any */
// Uploads are stored on the backend (Render + Postgres) so every visitor sees them.
const API_BASE = 'https://assisi-ifl-web-1.onrender.com';

export const B2_WINNER_TYPE = 'b2_winner';
export const GALLERY_TYPE = 'gallery';
export type GalleryAlbum = 'gallery' | 'tschuss';
export type GalleryKind = 'photo' | 'video' | 'youtube';

export interface GalleryItem {
  id: number;
  title: string;
  album: GalleryAlbum;
  kind: GalleryKind;
  media_url: string | null;
  youtube_id: string | null;
  created_at: string | null;
}

export function parseYouTubeId(url: string): string | null {
  const m = url.trim().match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?(?:.*&)?v=|embed\/|shorts\/|live\/))([\w-]{11})/);
  return m ? m[1] : /^[\w-]{11}$/.test(url.trim()) ? url.trim() : null;
}

function toGalleryItem(u: any): GalleryItem {
  const [album, kind] = String(u.hashtags || 'gallery:photo').split(':') as [GalleryAlbum, GalleryKind];
  return {
    id: u.id,
    title: u.title,
    album: album === 'tschuss' ? 'tschuss' : 'gallery',
    kind: kind === 'youtube' || kind === 'video' ? kind : 'photo',
    media_url: u.media_url,
    youtube_id: kind === 'youtube' ? parseYouTubeId(u.content || '') : null,
    created_at: u.created_at,
  };
}

export async function getGallery(album?: GalleryAlbum): Promise<GalleryItem[]> {
  try {
    const all = await fetchAllUploads();
    return all
      .filter((u) => u.type === GALLERY_TYPE)
      .map(toGalleryItem)
      .filter((g) => (!album || g.album === album) && (g.media_url || g.youtube_id));
  } catch (error) {
    console.error('Error getting gallery:', error);
    return [];
  }
}

export async function saveGalleryItem(opts: {
  album: GalleryAlbum;
  title: string;
  file?: File;
  youtubeUrl?: string;
}): Promise<void> {
  const kind: GalleryKind = opts.youtubeUrl ? 'youtube' : opts.file?.type.startsWith('video/') ? 'video' : 'photo';
  await saveUpload({
    title: opts.title || 'Untitled',
    content: opts.youtubeUrl || '',
    type: GALLERY_TYPE,
    institution_name: opts.album === 'tschuss' ? 'Tschüss Gallery' : 'Assisi Gallery',
    hashtags: `${opts.album}:${kind}`,
    mediaBlob: opts.file,
  });
}

async function fetchAllUploads(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/uploads`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

export async function getUploads(): Promise<any[]> {
  try {
    const all = await fetchAllUploads();
    return all.filter((u) => u.type !== B2_WINNER_TYPE && u.type !== GALLERY_TYPE);
  } catch (error) {
    console.error('Error getting uploads:', error);
    return [];
  }
}

export async function getB2Winners(): Promise<any[]> {
  try {
    const all = await fetchAllUploads();
    return all.filter((u) => u.type === B2_WINNER_TYPE && u.media_url);
  } catch (error) {
    console.error('Error getting B2 winners:', error);
    return [];
  }
}

export async function saveUpload(newContent: any): Promise<void> {
  const form = new FormData();
  form.append('title', newContent.title || 'Untitled');
  form.append('content', newContent.content || '');
  form.append('type', newContent.type || 'media');
  form.append('institution_name', newContent.institution_name || 'Assisi Institute');
  form.append('institution_id', String(newContent.institution_id || 1));
  form.append('hashtags', newContent.hashtags || '');
  if (newContent.mediaBlob) form.append('file', newContent.mediaBlob);

  const res = await fetch(`${API_BASE}/uploads`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(`Upload failed (HTTP ${res.status}): ${await res.text()}`);
}

export async function deleteUpload(id: number): Promise<void> {
  try {
    await fetch(`${API_BASE}/uploads/${id}`, { method: 'DELETE' });
  } catch (error) {
    console.error('Error deleting upload:', error);
  }
}

// ── Reviews ─────────────────────────────────────────────────────────────────
export const REVIEW_TYPE = 'review';

export interface Review {
  id: number;
  name: string;
  text: string;
  rating: number;
  created_at: string | null;
}

function toReview(u: any): Review {
  const rating = parseInt(String(u.hashtags || '5').replace('rating:', ''), 10) || 5;
  return { id: u.id, name: u.title, text: u.content, rating: Math.min(5, Math.max(1, rating)), created_at: u.created_at };
}

export async function getReviews(): Promise<Review[]> {
  try {
    const all = await fetchAllUploads();
    return all.filter((u) => u.type === REVIEW_TYPE).map(toReview);
  } catch (e) { console.error('Error fetching reviews:', e); return []; }
}

export async function saveReview(name: string, text: string, rating: number): Promise<void> {
  await saveUpload({ title: name, content: text, type: REVIEW_TYPE, institution_name: 'Visitor Review', hashtags: `rating:${rating}` });
}

export async function updateReview(id: number, name: string, text: string, rating: number): Promise<void> {
  await fetch(`${API_BASE}/uploads/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: name, content: text, hashtags: `rating:${rating}` }),
  });
}
