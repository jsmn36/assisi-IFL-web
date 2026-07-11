import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getItems, getItemMovements, recordMovement, updateItem } from '@/api/inventory';
import { StockLevelBar } from '../components/StockLevelBar';

const MANUAL_TYPES = ['adjustment', 'waste', 'transfer', 'return'];

export default function ItemDetailPage() {
  const { id } = useParams<{ id: string }>();
  const itemId = parseInt(id!);
  const navigate = useNavigate();
  const qc = useQueryClient();

  const [page, setPage] = useState(1);
  const [movForm, setMovForm] = useState({ movement_type: 'adjustment', quantity_delta: '', notes: '' });
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState<any>({});

  const { data: itemsPage } = useQuery({
    queryKey: ['inv-item', itemId],
    queryFn: () => getItems({ page_size: 200 }),
  });
  const item = itemsPage?.items?.find((i: any) => i.id === itemId);

  const { data: movPage } = useQuery({
    queryKey: ['inv-movements', itemId, page],
    queryFn: () => getItemMovements(itemId, { page, page_size: 20 }),
    enabled: !!itemId,
  });

  const movMut = useMutation({
    mutationFn: recordMovement,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inv-movements', itemId] });
      qc.invalidateQueries({ queryKey: ['inv-item', itemId] });
      qc.invalidateQueries({ queryKey: ['inv-items'] });
      setMovForm({ movement_type: 'adjustment', quantity_delta: '', notes: '' });
    },
  });

  const editMut = useMutation({
    mutationFn: (data: any) => updateItem(itemId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inv-item', itemId] });
      qc.invalidateQueries({ queryKey: ['inv-items'] });
      setEditing(false);
    },
  });

  if (!item) return <div className="p-6 text-gray-400">Loading item...</div>;

  const movements = movPage?.items || [];
  const totalPages = movPage ? Math.ceil(movPage.total / 20) : 1;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <button 
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-sm text-gray-500 hover:text-blue-600 transition-colors font-medium"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Inventory
      </button>

      {/* Item info card */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">{item.name}</h1>
            <p className="text-gray-500 font-mono text-sm mt-0.5">{item.sku}</p>
          </div>
          <button
            onClick={() => { setEditing(!editing); setEditForm({ name: item.name, unit_cost: item.unit_cost, reorder_point: item.reorder_point, reorder_quantity: item.reorder_quantity }); }}
            className="text-sm text-blue-600 hover:underline"
          >
            {editing ? 'Cancel' : 'Edit'}
          </button>
        </div>

        {editing ? (
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500">Name</label>
              <input value={editForm.name} onChange={e => setEditForm((f: any) => ({ ...f, name: e.target.value }))} className="w-full border rounded px-2 py-1 text-sm mt-1" />
            </div>
            <div>
              <label className="text-xs text-gray-500">Unit Cost</label>
              <input type="number" value={editForm.unit_cost} onChange={e => setEditForm((f: any) => ({ ...f, unit_cost: e.target.value }))} className="w-full border rounded px-2 py-1 text-sm mt-1" />
            </div>
            <div>
              <label className="text-xs text-gray-500">Reorder Point</label>
              <input type="number" value={editForm.reorder_point} onChange={e => setEditForm((f: any) => ({ ...f, reorder_point: e.target.value }))} className="w-full border rounded px-2 py-1 text-sm mt-1" />
            </div>
            <div>
              <label className="text-xs text-gray-500">Reorder Qty</label>
              <input type="number" value={editForm.reorder_quantity} onChange={e => setEditForm((f: any) => ({ ...f, reorder_quantity: e.target.value }))} className="w-full border rounded px-2 py-1 text-sm mt-1" />
            </div>
            <div className="col-span-2">
              <button onClick={() => editMut.mutate(editForm)} disabled={editMut.isPending} className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm">Save</button>
            </div>
          </div>
        ) : (
          <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
            <div><span className="text-gray-500">Unit:</span> {item.unit}</div>
            <div><span className="text-gray-500">Unit Cost:</span> ${parseFloat(item.unit_cost).toFixed(2)}</div>
            <div><span className="text-gray-500">Reorder At:</span> {item.reorder_point}</div>
            <div><span className="text-gray-500">Reorder Qty:</span> {item.reorder_quantity}</div>
            {item.pos_menu_item_id && <div><span className="text-gray-500">POS Item ID:</span> {item.pos_menu_item_id}</div>}
          </div>
        )}

        {/* Current quantity — prominent */}
        <div className="mt-4 flex items-end gap-4">
          <div>
            <p className="text-xs text-gray-500 uppercase">Current Stock</p>
            <p className={`text-4xl font-bold ${parseFloat(item.current_quantity) <= 0 ? 'text-red-600' : parseFloat(item.current_quantity) <= parseFloat(item.reorder_point) ? 'text-amber-600' : 'text-green-600'}`}>
              {parseFloat(item.current_quantity).toFixed(1)}
              <span className="text-lg font-normal text-gray-400 ml-1">{item.unit}</span>
            </p>
          </div>
          <div className="flex-1 pb-2">
            <StockLevelBar current={parseFloat(item.current_quantity)} reorderPoint={parseFloat(item.reorder_point)} />
          </div>
        </div>
      </div>

      {/* Manual adjustment */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-3">Record Adjustment</h2>
        <div className="grid grid-cols-3 gap-3">
          <select value={movForm.movement_type} onChange={e => setMovForm(f => ({ ...f, movement_type: e.target.value }))} className="border rounded px-3 py-2 text-sm">
            {MANUAL_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <input
            type="number"
            value={movForm.quantity_delta}
            onChange={e => setMovForm(f => ({ ...f, quantity_delta: e.target.value }))}
            placeholder="Quantity (+ in, - out)"
            className="border rounded px-3 py-2 text-sm"
          />
          <input
            value={movForm.notes}
            onChange={e => setMovForm(f => ({ ...f, notes: e.target.value }))}
            placeholder="Notes (optional)"
            className="border rounded px-3 py-2 text-sm"
          />
        </div>
        <button
          onClick={() => movMut.mutate({ item_id: itemId, ...movForm, quantity_delta: parseFloat(movForm.quantity_delta) })}
          disabled={!movForm.quantity_delta || movMut.isPending}
          className="mt-3 bg-amber-500 hover:bg-amber-600 disabled:bg-gray-300 text-white px-4 py-2 rounded text-sm font-medium"
        >
          {movMut.isPending ? 'Saving...' : 'Record Movement'}
        </button>
        {movMut.isError && <p className="mt-2 text-red-600 text-sm">{String((movMut.error as any)?.response?.data?.detail || 'Error')}</p>}
      </div>

      {/* Movement history */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">Movement History</h2>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase">
            <tr>
              <th className="px-4 py-3 text-left">Date</th>
              <th className="px-4 py-3 text-left">Type</th>
              <th className="px-4 py-3 text-right">Delta</th>
              <th className="px-4 py-3 text-right">Unit Cost</th>
              <th className="px-4 py-3 text-left">Reference</th>
              <th className="px-4 py-3 text-left">By</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {movements.map((m: any) => (
              <tr key={m.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-xs text-gray-500">{new Date(m.created_at).toLocaleString()}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-700">{m.movement_type}</span>
                </td>
                <td className={`px-4 py-3 text-right font-semibold ${parseFloat(m.quantity_delta) > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {parseFloat(m.quantity_delta) > 0 ? '+' : ''}{parseFloat(m.quantity_delta).toFixed(3)}
                </td>
                <td className="px-4 py-3 text-right text-gray-500">${parseFloat(m.unit_cost).toFixed(2)}</td>
                <td className="px-4 py-3 text-xs text-gray-500">{m.reference || '—'}</td>
                <td className="px-4 py-3 text-xs text-gray-500">{m.created_by}</td>
              </tr>
            ))}
            {movements.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">No movements</td></tr>
            )}
          </tbody>
        </table>
        {totalPages > 1 && (
          <div className="px-4 py-3 flex gap-2 justify-end border-t">
            <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="text-sm text-blue-600 disabled:text-gray-300">← Prev</button>
            <span className="text-sm text-gray-500">{page} / {totalPages}</span>
            <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)} className="text-sm text-blue-600 disabled:text-gray-300">Next →</button>
          </div>
        )}
      </div>
    </div>
  );
}
