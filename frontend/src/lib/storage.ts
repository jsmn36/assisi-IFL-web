import { get, set } from 'idb-keyval';

const UPLOADS_KEY = 'assisi_uploads';

export async function getUploads(): Promise<any[]> {
  try {
    const data = await get(UPLOADS_KEY);
    if (!data) return [];
    
    // Regenerate object URLs from stored blobs to ensure they are valid in current session
    return data.map((item: any) => {
      if (item.mediaBlob) {
        // Only generate a new object URL if we don't have one or if we just loaded from IDB
        item.media_url = URL.createObjectURL(item.mediaBlob);
      }
      return item;
    });
  } catch (error) {
    console.error('Error getting uploads:', error);
    return [];
  }
}

export async function saveUpload(newContent: any): Promise<void> {
  try {
    const data = await get(UPLOADS_KEY) || [];
    const updated = [newContent, ...data];
    await set(UPLOADS_KEY, updated);
  } catch (error) {
    console.error('Error saving upload:', error);
  }
}

export async function deleteUpload(id: number): Promise<void> {
  try {
    const data = await get(UPLOADS_KEY) || [];
    const updated = data.filter((item: any) => item.id !== id);
    await set(UPLOADS_KEY, updated);
  } catch (error) {
    console.error('Error deleting upload:', error);
  }
}
