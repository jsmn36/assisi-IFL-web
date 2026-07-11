interface Props {
  icon?: string;
  title: string;
  message: string;
  action?: { label: string; onClick: () => void };
}

export function EmptyState({ icon = '📭', title, message, action }: Props) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      padding: '48px 24px', textAlign: 'center',
    }}>
      <div style={{ fontSize: 40, marginBottom: 12 }}>{icon}</div>
      <div style={{ fontSize: 16, fontWeight: 600, color: '#111827', marginBottom: 6 }}>
        {title}
      </div>
      <div style={{ fontSize: 14, color: '#6b7280', maxWidth: 320, lineHeight: 1.5 }}>
        {message}
      </div>
      {action && (
        <button
          onClick={action.onClick}
          style={{
            marginTop: 16, padding: '8px 16px',
            background: '#0F2040', color: '#fff',
            border: 'none', borderRadius: 6,
            cursor: 'pointer', fontSize: 14,
            fontFamily: 'inherit', fontWeight: 500,
          }}
        >
          {action.label}
        </button>
      )}
    </div>
  );
}