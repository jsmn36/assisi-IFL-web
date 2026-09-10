interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function Spinner({ size = 'md', className = '' }: SpinnerProps) {
  const sizes = { sm: 'h-4 w-4', md: 'h-8 w-8', lg: 'h-12 w-12' };
  return (
    <div className={`animate-spin rounded-full border-2 border-gray-300 border-t-blue-600 ${sizes[size]} ${className}`} />
  );
}

export function LoadingPage() {
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-center">
        <Spinner size="lg" />
        <p className="mt-4 text-gray-500">Loading...</p>
      </div>
    </div>
  );
}

export function LoadingOverlay() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div className="rounded-lg bg-white p-6 text-center shadow-xl">
        <Spinner size="lg" />
        <p className="mt-4 text-gray-500">Processing...</p>
      </div>
    </div>
  );
}

export default function Loading() {
  return (
    <div className="flex items-center justify-center p-8">
      <Spinner size="lg" />
    </div>
  );
}
