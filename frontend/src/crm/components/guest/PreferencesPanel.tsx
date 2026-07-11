import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { GuestPreference } from '../../types/crm';
import { crmPreferencesApi } from '../../api/crmClient';
import { EmptyState } from '../shared/EmptyState';
import { usePermissions } from '../../hooks/usePermissions';

interface Props {
  guestId: number;
  preferences: GuestPreference | null;
}

export function PreferencesPanel({ guestId, preferences }: Props) {
  const { can } = usePermissions();
  const qc = useQueryClient();
  const [editing, setEditing]   = useState(false);
  const [form, setForm]         = useState({
    room_preference: preferences?.room_preference ?? '',
    dietary_restrictions: preferences?.dietary_restrictions ?? '',
    special_occasions: preferences?.special_occasions ?? '',
    other_notes: preferences?.other_notes ?? '',
  });

  const { mutateAsync, isPending } = useMutation({
    mutationFn: (data: typeof form) => crmPreferencesApi.update(guestId, {
      room_preference: data.room_preference || null,
      dietary_restrictions: data.dietary_restrictions || null,
      special_occasions: data.special_occasions || null,
      other_notes: data.other_notes || null,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['crm', 'guest', guestId] });
      setEditing(false);
    },
  });

  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '8px 10px', border: '1px solid #d1d5db',
    borderRadius: 6, fontSize: 14, fontFamily: 'inherit', boxSizing: 'border-box',
  };

  const fields = [
    { key: 'room_preference' as const,     label: '🏨 Room Preference',     placeholder: 'e.g. High floor, quiet, away from elevator' },
    { key: 'dietary_restrictions' as const, label: '🍽️ Dietary Restrictions', placeholder: 'e.g. Vegetarian, gluten-free' },
    { key: 'special_occasions' as const,    label: '🎉 Special Occasions',    placeholder: 'e.g. Birthday March 22, anniversary October 14' },
    { key: 'other_notes' as const,          label: '📋 Other Notes',          placeholder: 'Any other relevant preferences' },
  ];

  if (!preferences && !editing) {
    return (
      <div style={{ padding: 24 }}>
        <EmptyState
          icon="⚙️"
          title="No preferences recorded"
          message="Add room preferences, dietary requirements, and special occasion notes for this guest."
          action={can('add_notes') ? { label: 'Add Preferences', onClick: () => setEditing(true) } : undefined}
        />
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>Guest Preferences</h3>
        {can('add_notes') && !editing && (
          <button onClick={() => setEditing(true)} style={{ padding: '7px 14px', background: 'transparent', border: '1px solid #d1d5db', borderRadius: 6, cursor: 'pointer', fontSize: 13, fontFamily: 'inherit' }}>
            Edit
          </button>
        )}
      </div>

      {editing ? (
        <div>
          {fields.map(f => (
            <div key={f.key} style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 6, color: '#374151' }}>{f.label}</label>
              <input
                type="text"
                value={form[f.key]}
                onChange={e => setForm(prev => ({ ...prev, [f.key]: e.target.value }))}
                placeholder={f.placeholder}
                style={inputStyle}
              />
            </div>
          ))}
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            <button onClick={() => setEditing(false)} style={{ padding: '8px 16px', background: '#fff', border: '1px solid #d1d5db', borderRadius: 6, cursor: 'pointer', fontFamily: 'inherit' }}>Cancel</button>
            <button onClick={() => mutateAsync(form)} disabled={isPending} style={{ padding: '8px 16px', background: '#0F2040', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontFamily: 'inherit' }}>
              {isPending ? 'Saving…' : 'Save Preferences'}
            </button>
          </div>
        </div>
      ) : (
        <div>
          {fields.map(f => (
            <div key={f.key} style={{ marginBottom: 16, display: 'flex', gap: 12 }}>
              <div style={{ width: 180, fontSize: 13, color: '#6b7280', flexShrink: 0, paddingTop: 2 }}>{f.label}</div>
              <div style={{ fontSize: 14, color: preferences?.[f.key] ? '#111827' : '#d1d5db' }}>
                {preferences?.[f.key] ?? 'Not set'}
              </div>
            </div>
          ))}
          {preferences?.updated_at && (
            <div style={{ marginTop: 16, fontSize: 11, color: '#9ca3af' }}>
              Last updated {new Date(preferences.updated_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
