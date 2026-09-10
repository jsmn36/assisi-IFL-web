/**
 * Lazy Load Component
 * Lazy load any component based on its visibility in the viewport.
 */
import { useState, useEffect, useRef, type ReactNode } from 'react';

interface LazyLoadProps {
  children: ReactNode;
  placeholder?: ReactNode;
  threshold?: number;
  rootMargin?: string;
  className?: string;
}

export function LazyLoad({
  children,
  placeholder,
  threshold = 0.01,
  rootMargin = '150px',
  className = '',
}: LazyLoadProps) {
  const [isVisible, setIsVisible] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible(true);
            observer.unobserve(entry.target);
          }
        });
      },
      {
        threshold,
        rootMargin,
      }
    );

    observer.observe(containerRef.current);

    return () => {
      if (containerRef.current) {
        observer.unobserve(containerRef.current);
      }
    };
  }, [threshold, rootMargin]);

  return (
    <div ref={containerRef} className={className}>
      {isVisible ? (
        children
      ) : (
        placeholder || <div className="h-40 bg-gray-50/50 animate-pulse rounded-2xl border border-dashed border-gray-100" />
      )}
    </div>
  );
}
