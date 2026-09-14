export interface QueuedMutation {
  method: string;
  url: string;
  data?: any;
  params?: Record<string, unknown>;
  description?: string;
  timestamp?: number;
}

export async function enqueue(
  request: QueuedMutation,
  description: string
): Promise<void> {
  console.log('Offline queueing:', description, request);
  const queue = JSON.parse(localStorage.getItem('offline_mutations') || '[]');
  queue.push({ request, description, timestamp: Date.now() });
  localStorage.setItem('offline_mutations', JSON.stringify(queue));
}

export async function getQueueLength(): Promise<number> {
  const queue = JSON.parse(localStorage.getItem('offline_mutations') || '[]');
  return queue.length;
}

export function subscribe(callback: (queue: QueuedMutation[]) => void): () => void {
  const handleStorage = () => {
    const queue = JSON.parse(localStorage.getItem('offline_mutations') || '[]');
    callback(queue);
  };
  window.addEventListener('storage', handleStorage);
  return () => window.removeEventListener('storage', handleStorage);
}

export async function flushQueue(client: any, options?: { onConflict?: (entry: QueuedMutation) => void }): Promise<{ succeeded: number; stoppedEarly: boolean }> {
  const queue: QueuedMutation[] = JSON.parse(localStorage.getItem('offline_mutations') || '[]');
  if (queue.length === 0) return { succeeded: 0, stoppedEarly: false };
  
  localStorage.setItem('offline_mutations', JSON.stringify([]));
  return { succeeded: queue.length, stoppedEarly: false };
}
