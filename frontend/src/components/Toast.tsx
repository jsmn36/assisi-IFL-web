import { useEffect, createContext, useContext, useState, type ReactNode } from 'react';
import { X, CheckCircle, AlertCircle, Info, BellRing } from 'lucide-react';

interface AlertProps {
  id: number;
  message: string;
  type?: 'success' | 'error' | 'info';
  onClose: () => void;
}

export function PopOutAlert({ message, type = 'info', onClose }: AlertProps) {
  const icons = {
    success: <CheckCircle className="h-12 w-12 text-green-500" />,
    error: <AlertCircle className="h-12 w-12 text-red-500" />,
    info: <Info className="h-12 w-12 text-blue-500" />,
  };

  const accentColors = {
    success: 'bg-green-500',
    error: 'bg-red-500',
    info: 'bg-blue-500',
  };

  useEffect(() => {
    const duration = type === 'error' ? 7000 : 4000;
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [type, onClose]);

  return (
    <div className="fixed inset-0 z-[1000] flex items-center justify-center p-4 pointer-events-none">
      <div className="absolute inset-0 bg-black/5 backdrop-blur-[2px] pointer-events-auto" onClick={onClose} />
      <div className={`
        relative w-full max-w-sm bg-white/90 backdrop-blur-xl rounded-[2.5rem] shadow-[0_20px_50px_rgba(0,0,0,0.15)] border border-white/50
        p-8 flex flex-col items-center text-center overflow-hidden animate-in zoom-in-95 fade-in duration-300 slide-in-from-bottom-10
        pointer-events-auto
      `}>
        <div className={`absolute top-0 inset-x-0 h-2 ${accentColors[type]}`} />
        <div className="absolute -top-3 -right-3 opacity-5 rotate-12">
          <BellRing className="h-24 w-24" />
        </div>
        <div className="mb-6 bg-white p-4 rounded-3xl shadow-inner border border-gray-100 flex items-center justify-center">
          {icons[type]}
        </div>
        <div className="space-y-4">
          <h3 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.3em] pl-1">NOTIFICATION</h3>
          <p className="text-xl font-bold text-gray-900 leading-tight">
            {message}
          </p>
        </div>
        <button 
          onClick={onClose}
          className="mt-8 px-8 py-3 bg-gray-900 text-white rounded-2xl text-xs font-black uppercase tracking-widest hover:scale-105 active:scale-95 transition-all shadow-xl shadow-gray-200"
        >
          DISMISS
        </button>
        <button 
          onClick={onClose}
          className="absolute top-6 right-6 text-gray-300 hover:text-gray-900 transition-colors"
        >
          <X className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}

interface ToastContextType {
  showToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [alerts, setAlerts] = useState<Array<{ id: number; message: string; type: 'success' | 'error' | 'info' }>>([]);

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = Date.now();
    setAlerts((prev) => [...prev, { id, message, type }]);
  };

  const removeAlert = (id: number) => {
    setAlerts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed inset-0 pointer-events-none z-[1000]">
        {alerts.map((alert, index) => (
          <div key={alert.id} style={{ zIndex: 1000 + index }}>
             <PopOutAlert 
                id={alert.id}
                message={alert.message} 
                type={alert.type} 
                onClose={() => removeAlert(alert.id)} 
              />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
}
