/**
 * Action Sheet Component
 * Mobile bottom sheet for actions
 */
import { type ReactNode } from 'react';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Action {
  label: string;
  onClick: () => void;
  icon?: ReactNode;
  variant?: 'default' | 'danger';
  disabled?: boolean;
}

interface ActionSheetProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  actions: Action[];
}

export function ActionSheet({
  isOpen,
  onClose,
  title,
  actions,
}: ActionSheetProps) {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-[100] backdrop-blur-sm animate-in fade-in duration-300"
        onClick={onClose}
      />

      {/* Sheet */}
      <div className="fixed bottom-0 left-0 right-0 bg-white rounded-t-3xl z-[101] animate-slide-up max-h-[90vh] overflow-y-auto shadow-2xl safe-area-bottom">
        {/* Handle for dragging (visual only) */}
        <div className="w-12 h-1.5 bg-gray-200 rounded-full mx-auto mt-3 mb-1" />

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h3 className="font-bold text-xl text-gray-900">{title || 'Actions'}</h3>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors active:scale-95"
          >
            <X className="h-6 w-6 text-gray-500" />
          </button>
        </div>

        {/* Actions */}
        <div className="py-2">
          {actions.map((action, index) => (
            <button
              key={index}
              onClick={() => {
                if (!action.disabled) {
                  action.onClick();
                  onClose();
                }
              }}
              disabled={action.disabled}
              className={cn(
                'w-full flex items-center gap-4 px-6 py-5 text-left transition-colors',
                action.disabled
                  ? 'opacity-40 cursor-not-allowed'
                  : 'active:bg-gray-100',
                action.variant === 'danger'
                  ? 'text-red-600'
                  : 'text-gray-900 border-b border-gray-50 last:border-0'
              )}
            >
              {action.icon && <span className="flex-shrink-0 text-gray-500">{action.icon}</span>}
              <span className="text-lg font-medium">{action.label}</span>
            </button>
          ))}
        </div>

        {/* Cancel Button */}
        <div className="p-6">
          <button
            onClick={onClose}
            className="w-full py-4 text-center font-bold text-gray-700 bg-gray-100 rounded-2xl active:bg-gray-200 active:scale-[0.98] transition-all"
          >
            Cancel
          </button>
        </div>
      </div>
    </>
  );
}
