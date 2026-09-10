import { Trash2, X } from 'lucide-react';

interface Props {
  count: number;
  onDelete: () => void;
  onClear: () => void;
  deleting?: boolean;
  entityName?: string;
}

export function BulkActionBar({ count, onDelete, onClear, deleting, entityName = 'item' }: Props) {
  if (count === 0) return null;
  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-4 bg-gray-900 text-white px-6 py-3 rounded-full shadow-2xl animate-in slide-in-from-bottom-4 duration-200">
      <span className="font-semibold text-sm">
        {count} {entityName}{count !== 1 ? 's' : ''} selected
      </span>
      <button
        onClick={onDelete}
        disabled={deleting}
        className="flex items-center gap-1.5 text-sm text-red-400 hover:text-red-300 disabled:opacity-50 transition-colors font-medium"
      >
        <Trash2 className="h-4 w-4" />
        {deleting ? 'Deleting…' : 'Delete Selected'}
      </button>
      <button
        onClick={onClear}
        className="text-gray-400 hover:text-white transition-colors ml-1"
        title="Clear selection"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
