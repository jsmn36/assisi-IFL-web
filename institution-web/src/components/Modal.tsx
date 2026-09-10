import { type ReactNode, useEffect } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  children: ReactNode;
}

const sizes = { 
  sm: 'max-w-md', 
  md: 'max-w-lg', 
  lg: 'max-w-2xl', 
  xl: 'max-w-4xl' 
};

export function Modal({ isOpen, onClose, title, size = 'md', children }: ModalProps) {
  useEffect(() => {
    document.body.style.overflow = isOpen ? 'hidden' : 'unset';
    
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    
    if (isOpen) window.addEventListener('keydown', handleKeyDown);
    
    return () => { 
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      
      {/* Modal */}
      <div className={`relative z-50 w-full bg-white rounded-lg shadow-xl ${sizes[size]} mx-4 max-h-[90vh] overflow-y-auto`}>
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-xl font-semibold">{title || 'Modal'}</h2>
          <button 
            onClick={onClose} 
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        
        {/* Content */}
        <div className="px-6 py-4">{children}</div>
      </div>
    </div>
  );
}
