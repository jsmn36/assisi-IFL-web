import { useEffect, useRef } from 'react';
import { useCRMStore } from '../../store/crmStore';

interface Props {
  placeholder?: string;
}

export function SearchBar({ placeholder = 'Search by name, email, or phone…' }: Props) {
  const { filters, setSearch } = useCRMStore();
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const value = e.target.value;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setSearch(value), 300);
  }

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  return (
    <div style={{ position: 'relative', flexShrink: 0 }}>
      <span style={{
        position: 'absolute', left: 12, top: '50%',
        transform: 'translateY(-50%)', fontSize: 14,
        color: '#9ca3af', pointerEvents: 'none',
      }}>
        🔍
      </span>
      <input
        type="text"
        defaultValue={filters.search}
        onChange={handleChange}
        placeholder={placeholder}
        style={{
          paddingLeft: 36, paddingRight: 12,
          paddingTop: 8, paddingBottom: 8,
          border: '1px solid #d1d5db', borderRadius: 6,
          fontSize: 14, width: 280, outline: 'none',
          fontFamily: 'inherit', background: '#fff',
          boxSizing: 'border-box',
        }}
      />
    </div>
  );
}