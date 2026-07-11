import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useGuestDetail } from '../hooks/useGuestDetail';
import { GuestProfile } from '../components/guest/GuestProfile';
import { StayHistory } from '../components/guest/StayHistory';
import { NotesList } from '../components/guest/NotesList';
import { PreferencesPanel } from '../components/guest/PreferencesPanel';
import { AddNoteModal } from '../components/guest/AddNoteModal';
import { SkeletonRow } from '../components/shared/SkeletonRow';
import { ErrorCard } from '../components/shared/ErrorCard';
import { usePermissions } from '../hooks/usePermissions';
import { useCRMStore } from '../store/crmStore';

export default function GuestDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const guestId = Number(id);
  const { data, isLoading, isError } = useGuestDetail(guestId);
  const { activeDetailTab, setActiveDetailTab, openAddNoteModal } = useCRMStore();
  const { can } = usePermissions();

  const TABS = ['stays', 'notes', 'preferences'] as const;

  if (isLoading) {
    return (
      <div>
        <div style={{ height: 20, width: 80, background: '#e5e7eb', borderRadius: 4, marginBottom: 12 }} />
        <div style={{ height: 200, background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, marginBottom: 20 }} />
        <div style={{ height: 42, borderBottom: '2px solid #e5e7eb', marginBottom: 20, display: 'flex', gap: 24, padding: '0 20px' }}>
          <div style={{ width: 60, height: '100%', background: '#f3f4f6' }} />
          <div style={{ width: 60, height: '100%', background: '#f3f4f6' }} />
          <div style={{ width: 60, height: '100%', background: '#f3f4f6' }} />
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <ErrorCard 
        message="Could not load profile. It may have been deleted or there is a connection issue." 
        onRetry={() => window.location.reload()} 
      />
    );
  }

  return (
    <div>
      {/* Back link */}
      <button
        onClick={() => navigate('/crm/guests')}
        style={{ background: 'none', border: 'none', color: '#6b7280', cursor: 'pointer', fontSize: 13, padding: '0 0 12px', fontFamily: 'inherit' }}
      >
        ← All Guests
      </button>

      <GuestProfile guest={data.guest} />

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 0, borderBottom: '2px solid #e5e7eb', marginBottom: 20 }}>
        {TABS.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveDetailTab(tab as any)}
            style={{
              padding: '10px 20px', background: 'none', border: 'none',
              fontSize: 14, cursor: 'pointer', fontFamily: 'inherit',
              fontWeight: activeDetailTab === tab ? 600 : 400,
              color: activeDetailTab === tab ? '#0F2040' : '#6b7280',
              borderBottom: activeDetailTab === tab ? '2px solid #0F2040' : '2px solid transparent',
              marginBottom: -2, textTransform: 'capitalize',
            }}
          >
            {tab === 'stays' && `Stays (${data.stays.length})`}
            {tab === 'notes' && `Notes (${data.notes.length})`}
            {tab === 'preferences' && 'Preferences'}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div style={{ background: '#fff', borderRadius: 8, border: '1px solid #e5e7eb', overflow: 'hidden' }}>
        {activeDetailTab === 'stays' && <StayHistory stays={data.stays} />}
        {activeDetailTab === 'notes' && (
          <NotesList
            notes={data.notes}
            onAddNote={() => openAddNoteModal(guestId)}
            canAdd={can('add_notes')}
          />
        )}
        {activeDetailTab === 'preferences' && (
          <PreferencesPanel guestId={guestId} preferences={data.preferences} />
        )}
      </div>

      <AddNoteModal />
    </div>
  );
}
