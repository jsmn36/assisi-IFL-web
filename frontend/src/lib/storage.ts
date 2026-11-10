/* eslint-disable @typescript-eslint/no-explicit-any */
// Uploads are stored on the backend (Render + Postgres) so every visitor sees them.
const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

export async function getUploads(): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE}/uploads`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (error) {
    console.error('Error getting uploads:', error);
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
  if (!res.ok) throw new Error(`Upload failed (HTTP ${res.status})`);
}

export async function deleteUpload(id: number): Promise<void> {
  try {
    await fetch(`${API_BASE}/uploads/${id}`, { method: 'DELETE' });
  } catch (error) {
    console.error('Error deleting upload:', error);
  }
}
