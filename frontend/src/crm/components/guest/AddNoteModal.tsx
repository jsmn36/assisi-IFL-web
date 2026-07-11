import React, { useState, useEffect } from 'react';
import { useAddNote } from '../../hooks/useNotes';
import { useCRMStore } from '../../store/crmStore';
import type { NoteType, NoteVisibility } from '../../types/crm';

// Validation (without Zod for portability — add Zod if preferred)
function validate(text: string, type: string): string | null {
  if (!type) return 'Please select a note type.';
  const trimmed = text.trim();
  if (trimmed.length < 10) return 'Note must be at least 10 characters.';
  if (trimmed.length > 1000) return 'Note must be 1000 characters or less.';
  return null;
}

export function AddNoteModal() {
  const { addNoteModalOpen, addNoteTargetGuestId, closeAddNoteModal } = useCRMStore();
  const { mutateAsync, isPending } = useAddNote(addNoteTargetGuestId ?? 0);

  const [noteType, setNoteType]     = useState<NoteType | ''>('');
  const [noteText, setNoteText]     = useState('');
  const [visibility, setVisibility] = useState<NoteVisibility>('internal');
  const [error, setError]           = useState<string | null>(null);
  const [isDirty, setIsDirty]       = useState(false);

  // Reset form when modal opens
  useEffect(() => {
    if (addNoteModalOpen) {
      setNoteType(''); setNoteText(''); setVisibility('internal');
      setError(null); setIsDirty(false);
    }
  }, [addNoteModalOpen]);

  if (!addNoteModalOpen || !addNoteTargetGuestId) return null;

  function handleClose() {
    if (isDirty && !window.confirm('Your note will be discarded. Continue?')) return;
    closeAddNoteModal();
  }

  async function handleSubmit() {
    const err = validate(noteText, noteType);
    if (err) { setError(err); return; }
    setError(null);
    try {
      await mutateAsync({ note_type: noteType as NoteType, note_text: noteText.trim(), visibility });
      closeAddNoteModal();
    } catch {
      setError('Failed to save note. Please try again.');
    }
  }

  const charCount = noteText.length;
  const selectStyle: React.CSSProperties = {
    width: '100%', padding: '8px 10px', border: '1px solid #d1d5db',
    borderRadius: 6, fontSize: 14, fontFamily: 'inherit', background: '#fff',
  };

  return (
    /* Backdrop */
    <div
      onClick={handleClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100,
      }}
    >
      {/* Modal */}
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: '#fff', borderRadius: 10, width: 480, maxWidth: '95vw',
          boxShadow: '0 20px 60px rgba(0,0,0,0.2)', overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div style={{ padding: '18px 24px', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>Add Note</h3>
          <button onClick={handleClose} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: '#9ca3af', lineHeight: 1 }}>×</button>
        </div>

        {/* Body */}
        <div style={{ padding: 24 }}>
          {/* Type */}
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 6, color: '#374151' }}>
              Note Type *
            </label>
            <select value={noteType} onChange={e => { setNoteType(e.target.value as NoteType); setIsDirty(true); }} style={selectStyle}>
              <option value="">Select type…</option>
              <option value="preference">Preference</option>
              <option value="vip">VIP</option>
              <option value="issue">Issue / Complaint</option>
              <option value="special_request">Special Request</option>
              <option value="general">General</option>
            </select>
          </div>

          {/* Text */}
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 6, color: '#374151' }}>
              Note *
            </label>
            <textarea
              value={noteText}
              onChange={e => { setNoteText(e.target.value); setIsDirty(true); }}
              rows={5}
              maxLength={1000}
              placeholder="Enter your note about this guest…"
              style={{ ...selectStyle, resize: 'vertical', lineHeight: 1.5 }}
            />
            <div style={{ fontSize: 11, color: charCount > 950 ? '#dc2626' : '#9ca3af', textAlign: 'right', marginTop: 4 }}>
              {charCount}/1000
            </div>
          </div>

          {/* Visibility */}
          <div style={{ marginBottom: 20 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 6, color: '#374151' }}>
              Visibility
            </label>
            <select value={visibility} onChange={e => setVisibility(e.target.value as NoteVisibility)} style={selectStyle}>
              <option value="internal">Internal Only (staff only)</option>
              <option value="guest_visible">Guest-Visible</option>
            </select>
          </div>

          {/* Error */}
          {error && <div style={{ padding: '10px 14px', background: '#fef2f2', color: '#dc2626', borderRadius: 6, fontSize: 13, marginBottom: 16 }}>{error}</div>}

          {/* Actions */}
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <button onClick={handleClose} style={{ padding: '9px 18px', background: '#fff', border: '1px solid #d1d5db', borderRadius: 6, cursor: 'pointer', fontSize: 14, fontFamily: 'inherit', color: '#374151' }}>
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isPending}
              style={{ padding: '9px 18px', background: isPending ? '#9ca3af' : '#0F2040', color: '#fff', border: 'none', borderRadius: 6, cursor: isPending ? 'not-allowed' : 'pointer', fontSize: 14, fontFamily: 'inherit', fontWeight: 600 }}
            >
              {isPending ? 'Saving…' : 'Save Note'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
