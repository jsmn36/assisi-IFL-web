import { Modal } from '@/components/Modal';
import { Button } from '@/components/Button';
import { AlertTriangle, Info, AlertCircle } from 'lucide-react';

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'info';
  loading?: boolean;
}

export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'warning',
  loading = false,
}: ConfirmDialogProps) {
  const icons = {
    danger: <AlertCircle className="h-6 w-6 text-red-600" />,
    warning: <AlertTriangle className="h-6 w-6 text-yellow-600" />,
    info: <Info className="h-6 w-6 text-blue-600" />,
  };

  const colors = {
    danger: 'bg-red-600 hover:bg-red-700',
    warning: 'bg-yellow-600 hover:bg-yellow-700',
    info: 'bg-blue-600 hover:bg-blue-700',
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
      <div className="space-y-4">
        <div className="flex items-start gap-3">
          {icons[variant]}
          <p className="text-gray-700">{message}</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={onClose} className="flex-1">
            {cancelText}
          </Button>
          <Button
            onClick={onConfirm}
            className={`flex-1 ${colors[variant]}`}
            disabled={loading}
          >
            {loading ? 'Processing...' : confirmText}
          </Button>
        </div>
      </div>
    </Modal>
  );
}