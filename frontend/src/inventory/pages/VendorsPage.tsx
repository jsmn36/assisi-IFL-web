import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getVendors, createVendor, updateVendor } from '@/api/inventory';

const BLANK = { name: '', contact_name: '', email: '', phone: '', address: '', payment_terms_days: '30' };

export default function VendorsPage() {
  const qc = useQueryClient();
  const [editing, setEditing] = useState<any>(null);
  const [form, setForm] = useState({ ...BLANK });
  const [panelOpen, setPanelOpen] = useState(false);

  const { data: vendors = [] } = useQuery({ queryKey: ['inv-vendors'], queryFn: getVendors });

  const saveMut = useMutation({
    mutationFn: (data: any) =>
      editing ? updateVendor(editing.id, data) : createVendor(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inv-vendors'] });
      setPanelOpen(false);
      setEditing(null);
      setForm({ ...BLANK });
    },
  });

  const openNew = () => { setEditing(null); setForm({ ...BLANK }); setPanelOpen(true); };
  const openEdit = (v: any) => { setEditing(v); setForm({ name: v.name, contact_name: v.contact_name || '', email: v.email || '', phone: v.phone || '', address: v.address || '', payment_terms_days: String(v.payment_terms_days) }); setPanelOpen(true); };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-800">Vendors</h1>
        <button onClick={openNew} className="bg-amber-500 hover:bg-amber-600 text-white px-4 py-2 rounded text-sm font-medium">+ New Vendor</button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase">
            <tr>
              <th className="px-4 py-3 text-left">Name</th>
              <th className="px-4 py-3 text-left">Contact</th>
              <th className="px-4 py-3 text-left">Email</th>
              <th className="px-4 py-3 text-left">Phone</th>
              <th className="px-4 py-3 text-right">Payment Terms</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {(vendors as any[]).map((v: any) => (
              <tr key={v.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{v.name}</td>
                <td className="px-4 py-3 text-gray-500">{v.contact_name || '—'}</td>
                <td className="px-4 py-3 text-gray-500">{v.email || '—'}</td>
                <td className="px-4 py-3 text-gray-500">{v.phone || '—'}</td>
                <td className="px-4 py-3 text-right text-gray-500">{v.payment_terms_days} days</td>
                <td className="px-4 py-3 text-right">
                  <button onClick={() => openEdit(v)} className="text-blue-600 hover:underline text-xs">Edit</button>
                </td>
              </tr>
            ))}
            {(vendors as any[]).length === 0 && <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">No vendors yet</td></tr>}
          </tbody>
        </table>
      </div>

      {/* Slide-in panel */}
      {panelOpen && (
        <div className="fixed inset-0 bg-black/30 flex justify-end z-40" onClick={() => setPanelOpen(false)}>
          <div className="bg-white w-96 h-full shadow-xl p-6 overflow-y-auto" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-semibold mb-4">{editing ? 'Edit Vendor' : 'New Vendor'}</h2>
            <div className="space-y-3">
              {[
                { key: 'name', label: 'Name *', type: 'text' },
                { key: 'contact_name', label: 'Contact Name', type: 'text' },
                { key: 'email', label: 'Email', type: 'email' },
                { key: 'phone', label: 'Phone', type: 'text' },
                { key: 'address', label: 'Address', type: 'text' },
                { key: 'payment_terms_days', label: 'Payment Terms (days)', type: 'number' },
              ].map(f => (
                <div key={f.key}>
                  <label className="text-xs text-gray-500">{f.label}</label>
                  <input
                    type={f.type}
                    value={(form as any)[f.key]}
                    onChange={e => setForm(prev => ({ ...prev, [f.key]: e.target.value }))}
                    className="w-full border rounded px-3 py-2 text-sm mt-1"
                  />
                </div>
              ))}
              <div className="flex gap-2 pt-2">
                <button onClick={() => setPanelOpen(false)} className="flex-1 border rounded py-2 text-sm">Cancel</button>
                <button
                  onClick={() => saveMut.mutate({ ...form, payment_terms_days: parseInt(form.payment_terms_days) })}
                  disabled={!form.name || saveMut.isPending}
                  className="flex-1 bg-amber-500 hover:bg-amber-600 disabled:bg-gray-300 text-white py-2 rounded text-sm font-medium"
                >
                  {saveMut.isPending ? 'Saving...' : 'Save'}
                </button>
              </div>
              {saveMut.isError && <p className="text-red-600 text-sm">{String((saveMut.error as any)?.response?.data?.detail || 'Error')}</p>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
