import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useCRMStore } from '../store/crmStore';
import { useCreateCampaign } from '../hooks/useCampaigns';
import { useSegments } from '../hooks/useSegments';
import type { SegmentName } from '../types/crm';
import { SEGMENT_META } from '../types/crm';

const VARIABLES = ['{first_name}', '{last_name}', '{loyalty_tier}'];

export default function CampaignBuilderPage() {
  const navigate = useNavigate();
  const { campaignWizardStep, campaignDraft, setCampaignWizardStep, updateCampaignDraft, resetCampaignDraft } = useCRMStore();
  const { data: segments } = useSegments();
  const { mutateAsync: createCampaign, isPending } = useCreateCampaign();

  const inputStyle: React.CSSProperties = { width: '100%', padding: '9px 12px', border: '1px solid #d1d5db', borderRadius: 6, fontSize: 14, fontFamily: 'inherit', boxSizing: 'border-box' };

  // Selected segment info
  const selectedSegment = segments?.find(s => s.segment_name === campaignDraft.segment);
  const recipientCount  = selectedSegment?.guest_count ?? 0;

  async function handleSend() {
    if (!campaignDraft.segment) return;
    try {
      await createCampaign({
        name: campaignDraft.name || `Campaign — ${campaignDraft.segment}`,
        segment_name: campaignDraft.segment as SegmentName | 'all',
        subject: campaignDraft.subject,
        preview_text: campaignDraft.previewText || null,
        body: campaignDraft.body,
        from_email: campaignDraft.fromEmail,
        from_name: campaignDraft.fromName,
      });
      resetCampaignDraft();
      navigate(`/crm/campaigns`);
    } catch {
      alert('Failed to save campaign. Please check required fields.');
    }
  }

  return (
    <div style={{ maxWidth: 660 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>New Campaign</h1>
        <button onClick={() => { resetCampaignDraft(); navigate('/crm/campaigns'); }} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6b7280', fontSize: 13, fontFamily: 'inherit' }}>Cancel</button>
      </div>

      {/* Step indicators */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 32 }}>
        {['Select Audience', 'Compose Email', 'Review & Send'].map((label, i) => {
          const step = (i + 1) as 1 | 2 | 3;
          const active = campaignWizardStep === step;
          const done   = campaignWizardStep > step;
          return (
            <div key={label} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 700, background: active ? '#0F2040' : done ? '#d1fae5' : '#f3f4f6', color: active ? '#fff' : done ? '#065f46' : '#9ca3af' }}>
                {done ? '✓' : step}
              </div>
              <div style={{ fontSize: 12, color: active ? '#0F2040' : '#9ca3af', fontWeight: active ? 600 : 400 }}>{label}</div>
            </div>
          );
        })}
      </div>

      {/* Step 1 */}
      {campaignWizardStep === 1 && (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 24 }}>
          <h3 style={{ margin: '0 0 16px' }}>Who receives this email?</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {segments?.map(s => (
              <label key={s.segment_name} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px', border: `2px solid ${campaignDraft.segment === s.segment_name ? '#0F2040' : '#e5e7eb'}`, borderRadius: 8, cursor: 'pointer', background: campaignDraft.segment === s.segment_name ? '#f0f4ff' : '#fff' }}>
                <input type="radio" name="segment" value={s.segment_name} checked={campaignDraft.segment === s.segment_name} onChange={() => updateCampaignDraft({ segment: s.segment_name as SegmentName })} style={{ accentColor: '#0F2040' }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{SEGMENT_META[s.segment_name].emoji} {SEGMENT_META[s.segment_name].label} <span style={{ fontWeight: 400, color: '#6b7280' }}>({s.guest_count} guests)</span></div>
                  <div style={{ fontSize: 12, color: '#9ca3af' }}>{SEGMENT_META[s.segment_name].criteria}</div>
                </div>
              </label>
            ))}
          </div>
          <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end' }}>
            <button onClick={() => setCampaignWizardStep(2)} disabled={!campaignDraft.segment} style={{ padding: '9px 20px', background: campaignDraft.segment ? '#0F2040' : '#fff', color: campaignDraft.segment ? '#fff' : '#9ca3af', border: campaignDraft.segment ? 'none' : '1px solid #e5e7eb', borderRadius: 6, cursor: campaignDraft.segment ? 'pointer' : 'not-allowed', fontFamily: 'inherit', fontWeight: 600 }}>
              Next: Compose →
            </button>
          </div>
        </div>
      )}

      {/* Step 2 */}
      {campaignWizardStep === 2 && (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 24 }}>
          <h3 style={{ margin: '0 0 20px' }}>Compose your email</h3>

          <div style={{ marginBottom: 14 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 6, color: '#374151' }}>Campaign Name</label>
            <input value={campaignDraft.name} onChange={e => updateCampaignDraft({ name: e.target.value })} placeholder="e.g. VIP Spring Offer 2026" style={inputStyle} />
          </div>
          <div style={{ marginBottom: 14 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 6, color: '#374151' }}>Subject Line *</label>
            <input value={campaignDraft.subject} onChange={e => updateCampaignDraft({ subject: e.target.value })} placeholder="e.g. Exclusive offer just for you, {first_name}" style={inputStyle} />
          </div>
          <div style={{ marginBottom: 14 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 6, color: '#374151' }}>Preview Text</label>
            <input value={campaignDraft.previewText} onChange={e => updateCampaignDraft({ previewText: e.target.value })} placeholder="Short preview shown in inbox…" style={inputStyle} />
          </div>
          <div style={{ marginBottom: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <label style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>Email Body *</label>
              <div style={{ display: 'flex', gap: 4 }}>
                {VARIABLES.map(v => (
                  <button key={v} onClick={() => updateCampaignDraft({ body: campaignDraft.body + v })} style={{ fontSize: 11, padding: '2px 8px', background: '#f3f4f6', border: '1px solid #d1d5db', borderRadius: 4, cursor: 'pointer', fontFamily: 'monospace' }}>{v}</button>
                ))}
              </div>
            </div>
            <textarea value={campaignDraft.body} onChange={e => updateCampaignDraft({ body: e.target.value })} rows={10} placeholder={`Dear {first_name},\n\n[Your message here]\n\nKind regards,\nThe Hotel Team`} style={{ ...inputStyle, resize: 'vertical', lineHeight: 1.6 }} />
          </div>

          <div style={{ display: 'flex', gap: 8, justifyContent: 'space-between', marginTop: 8 }}>
            <button onClick={() => setCampaignWizardStep(1)} style={{ padding: '9px 18px', background: '#fff', border: '1px solid #d1d5db', borderRadius: 6, cursor: 'pointer', fontFamily: 'inherit' }}>← Back</button>
            <button onClick={() => setCampaignWizardStep(3)} disabled={!campaignDraft.subject || !campaignDraft.body} style={{ padding: '9px 20px', background: '#0F2040', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontFamily: 'inherit', fontWeight: 600 }}>
              Review →
            </button>
          </div>
        </div>
      )}

      {/* Step 3 */}
      {campaignWizardStep === 3 && (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 24 }}>
          <h3 style={{ margin: '0 0 20px' }}>Review & Send</h3>
          <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, marginBottom: 20, fontSize: 14 }}>
            <div style={{ marginBottom: 8 }}><strong>Audience:</strong> {selectedSegment ? `${SEGMENT_META[selectedSegment.segment_name].label} (${recipientCount} guests)` : '—'}</div>
            <div style={{ marginBottom: 8 }}><strong>Subject:</strong> {campaignDraft.subject}</div>
            <div style={{ marginBottom: 8 }}><strong>From:</strong> {campaignDraft.fromName} &lt;{campaignDraft.fromEmail}&gt;</div>
            <div><strong>Body preview:</strong> <div style={{ marginTop: 4, fontSize: 13, color: '#6b7280', whiteSpace: 'pre-wrap', maxHeight: 100, overflow: 'hidden' }}>{campaignDraft.body.substring(0, 200)}…</div></div>
          </div>
          <div style={{ background: '#fef3c7', border: '1px solid #fde68a', borderRadius: 6, padding: '12px 16px', fontSize: 13, color: '#92400e', marginBottom: 20 }}>
            ⚠ Phase 1: Campaigns are saved as drafts. Real sending is enabled in Phase 2.
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'space-between' }}>
            <button onClick={() => setCampaignWizardStep(2)} style={{ padding: '9px 18px', background: '#fff', border: '1px solid #d1d5db', borderRadius: 6, cursor: 'pointer', fontFamily: 'inherit' }}>← Back</button>
            <button onClick={handleSend} disabled={isPending} style={{ padding: '9px 20px', background: isPending ? '#9ca3af' : '#0F2040', color: '#fff', border: 'none', borderRadius: 6, cursor: isPending ? 'not-allowed' : 'pointer', fontFamily: 'inherit', fontWeight: 600 }}>
              {isPending ? 'Saving…' : `Save Campaign (${recipientCount} recipients)`}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
