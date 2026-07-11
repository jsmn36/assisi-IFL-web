import { useCRMStore } from '../../store/crmStore';

interface Props {
  total: number;
  pages: number;
}

export function Pagination({ total, pages }: Props) {
  const { filters, setPage } = useCRMStore();
  const { page } = filters;

  if (pages <= 1) return null;

  const start = Math.min((page - 1) * 25 + 1, total);
  const end = Math.min(page * 25, total);

  return (
    <div style={{
      display: 'flex', alignItems: 'center',
      justifyContent: 'space-between', marginTop: 16,
      flexWrap: 'wrap', gap: 8,
    }}>
      <span style={{ fontSize: 13, color: '#6b7280' }}>
        Showing {start}–{end} of {total} guests
      </span>

      <div style={{ display: 'flex', gap: 4 }}>
        <PageBtn
          label="← Prev"
          onClick={() => setPage(page - 1)}
          disabled={page <= 1}
        />

        {Array.from({ length: Math.min(pages, 7) }, (_, i) => {
          const p = i + 1;
          return (
            <PageBtn
              key={p}
              label={String(p)}
              onClick={() => setPage(p)}
              disabled={false}
              active={p === page}
            />
          );
        })}

        <PageBtn
          label="Next →"
          onClick={() => setPage(page + 1)}
          disabled={page >= pages}
        />
      </div>
    </div>
  );
}

function PageBtn({
  label,
  onClick,
  disabled,
  active = false,
}: {
  label: string;
  onClick: () => void;
  disabled: boolean;
  active?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        padding: '5px 10px',
        border: '1px solid',
        borderColor: active ? '#0F2040' : '#d1d5db',
        borderRadius: 5,
        fontSize: 13,
        cursor: disabled ? 'not-allowed' : 'pointer',
        background: active ? '#0F2040' : '#fff',
        color: active ? '#fff' : disabled ? '#d1d5db' : '#374151',
        fontFamily: 'inherit',
        transition: 'all 0.1s',
      }}
    >
      {label}
    </button>
  );
}