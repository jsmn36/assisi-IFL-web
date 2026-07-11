import React from 'react';
import type { GuestNote, NoteType } from '../../types/crm';
import { EmptyState } from '../shared/EmptyState';

const NOTE_TYPE_STYLES: Record<NoteType, { bg: string; color: string; label: string }> = {
  preference:      { bg: '#eff6ff', color: '#1d4ed8', label: 'Preference' },
  issue:           { bg: '#fef2f2', color: '#dc2626', label: 'Issue' },
  vip:             { bg: '#fef3c7', color: '#92400e', label: 'VIP' },
  general:         { bg: '#f3f4f6', color: '#4b5563', label: 'General' },
  special_request: { bg: '#f0fdf4', color: '#166534', label: 'Special Request' },
};

interface Props {
  notes: GuestNote[];
  onAddNote: () => void;
  canAdd: boolean;
}

export function NotesList({ notes, onAddNote, canAdd }: Props) {
  if (!notes.length) {
    return (
      <div style={{ padding: 24 }}>
        <EmptyState
          icon="📝"
          title="No notes yet"
          message="Add notes about this guest's preferences, issues, or special requests."
          action={canAdd ? { label: 'Add First Note', onClick: onAddNote } : undefined}
        />
      </div>
    );
  }

  const sorted = [...notes].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', borderBottom: '1px solid #f3f4f6' }}>
        <span style={{ fontSize: 14, fontWeight: 600, color: '#374151' }}>{notes.length} note{notes.length !== 1 ? 's' : ''}</span>
        {canAdd && (
          <button
            onClick={onAddNote}
            style={{
              padding: '7px 14px', background: '#0F2040', color: '#fff',
              border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13, fontFamily: 'inherit',
            }}
          >
            + Add Note
          </button>
        )}
      </div>

      {/* Notes */}
      {sorted.map((note, idx) => {
        const style = NOTE_TYPE_STYLES[note.note_type];
        return (
          <div key={note.note_id} style={{
            padding: '16px 20px',
            borderBottom: idx < sorted.length - 1 ? '1px solid #f3f4f6' : 'none',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span style={{
                  fontSize: 11, padding: '2px 8px', borderRadius: 999,
                  background: style.bg, color: style.color, fontWeight: 600,
                }}>
                  {style.label}
                </span>
                {note.visibility === 'guest_visible' && (
                  <span style={{ fontSize: 11, color: '#9ca3af' }}>Guest-visible</span>
                )}
              </div>
              <div style={{ fontSize: 12, color: '#9ca3af', textAlign: 'right' }}>
                <div>{note.author}</div>
                <div>{new Date(note.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</div>
              </div>
            </div>
            <p style={{ margin: 0, fontSize: 14, color: '#374151', lineHeight: 1.5 }}>{note.note_text}</p>
          </div>
        );
      })}
    </div>
  );
}
