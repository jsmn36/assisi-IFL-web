import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getPurchaseOrders, getItems, getVendors, generatePurchaseOrders,
  updatePOStatus, receivePurchaseOrder, getReorderList,
} from '@/api/inventory';

const STATUS_BADGE: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  sent: 'bg-blue-100 text-blue-700',
  received: 'bg-green-100 text-green-700',
  partial: 'bg-amber-100 text-amber-700',
  cancelled: 'bg-red-100 text-red-600',
};

type Tab = 'all' | 'reorder';

function ReceiveModal({ po, onClose }: { po: any; onClose: () => void }) {
  const qc = useQueryClient();
  const [lines, setLines] = useState<Record<number, { qty: string; cost: string }>>(
    Object.fromEntries(po.lines.map((l: any) => [
      l.id,
      { qty: String(parseFloat(l.quantity_ordered) - parseFloat(l.quantity_received)), cost: String(l.unit_cost) },
    ]))
  );

  const mut = useMutation({
    mutationFn: () => receivePurchaseOrder(po.id, {
      lines: po.lines.map((l: any) => ({
        purchase_order_line_id: l.id,
        quantity_received: parseFloat(lines[l.id]?.qty || '0'),
        unit_cost: parseFloat(lines[l.id]?.cost || l.unit_cost),
      })),
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inv-pos'] });
      qc.invalidateQueries({ queryKey: ['inv-items'] });
      onClose();
    },
  });

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-lg">
        <h3 className="text-lg font-semibold mb-4">Receive Goods — PO #{po.id}</h3>
        <table className="w-full text-sm mb-4">
          <thead className="text-xs text-gray-500 uppercase">
            <tr>
              <th className="text-left py-1">Item</th>
              <th className="text-right py-1">Ordered</th>
              <th className="text-right py-1">Received</th>
              <th className="text-right py-1">Qty to Receive</th>
              <th className="text-right py-1">Unit Cost</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {po.lines.map((l: any) => (
              <tr key={l.id}>
                <td className="py-2">Item #{l.item_id}</td>
                <td className="text-right py-2">{l.quantity_ordered}</td>
                <td className="text-right py-2">{l.quantity_received}</td>
                <td className="text-right py-2">
                  <input
                    type="number"
                    value={lines[l.id]?.qty}
                    onChange={e => setLines(prev => ({ ...prev, [l.id]: { ...prev[l.id], qty: e.target.value } }))}
                    className="w-20 border rounded px-2 py-0.5 text-right text-sm"
                  />
                </td>
                <td className="text-right py-2">
                  <input
                    type="number"
                    value={lines[l.id]?.cost}
                    onChange={e => setLines(prev => ({ ...prev, [l.id]: { ...prev[l.id], cost: e.target.value } }))}
                    className="w-20 border rounded px-2 py-0.5 text-right text-sm"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="flex gap-2 justify-end">
          <button onClick={onClose} className="px-4 py-1.5 border rounded text-sm">Cancel</button>
          <button onClick={() => mut.mutate()} disabled={mut.isPending} className="px-4 py-1.5 bg-green-600 text-white rounded text-sm">
            {mut.isPending ? 'Saving...' : 'Confirm Receipt'}
          </button>
        </div>
        {mut.isError && <p className="mt-2 text-red-600 text-sm">{String((mut.error as any)?.response?.data?.detail || 'Error')}</p>}
      </div>
    </div>
  );
}

function PODrawer({ po, onClose }: { po: any; onClose: () => void }) {
  const qc = useQueryClient();
  const [showReceive, setShowReceive] = useState(false);

  const statusMut = useMutation({
    mutationFn: (status: string) => updatePOStatus(po.id, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inv-pos'] });
      onClose();
    },
  });

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-xl z-40 flex flex-col">
      <div className="flex items-center justify-between p-4 border-b">
        <h3 className="font-semibold">PO #{po.id}</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-700 text-xl">×</button>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="text-sm space-y-1">
          <div><span className="text-gray-500">Vendor:</span> #{po.vendor_id}</div>
          <div><span className="text-gray-500">Order Date:</span> {new Date(po.order_date).toLocaleDateString()}</div>
          {po.expected_delivery && <div><span className="text-gray-500">Expected:</span> {new Date(po.expected_delivery).toLocaleDateString()}</div>}
          {po.received_date && <div><span className="text-gray-500">Received:</span> {new Date(po.received_date).toLocaleDateString()}</div>}
          <div><span className="text-gray-500">Total:</span> <strong>${parseFloat(po.total_amount).toFixed(2)}</strong></div>
          <div><span className="text-gray-500">Status:</span> <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_BADGE[po.status]}`}>{po.status}</span></div>
        </div>

        <table className="w-full text-sm">
          <thead className="text-xs text-gray-500 uppercase border-b">
            <tr>
              <th className="text-left pb-1">Item</th>
              <th className="text-right pb-1">Ord.</th>
              <th className="text-right pb-1">Recv.</th>
              <th className="text-right pb-1">Cost</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {po.lines.map((l: any) => (
              <tr key={l.id}>
                <td className="py-1.5 text-xs">#{l.item_id}</td>
                <td className="text-right py-1.5">{l.quantity_ordered}</td>
                <td className="text-right py-1.5">{l.quantity_received}</td>
                <td className="text-right py-1.5">${parseFloat(l.unit_cost).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="p-4 border-t space-y-2">
        {po.status === 'draft' && (
          <button onClick={() => statusMut.mutate('sent')} disabled={statusMut.isPending} className="w-full bg-blue-600 text-white py-2 rounded text-sm font-medium">Mark as Sent</button>
        )}
        {po.status === 'sent' && (
          <>
            <button onClick={() => setShowReceive(true)} className="w-full bg-green-600 text-white py-2 rounded text-sm font-medium">Receive Goods</button>
            <button onClick={() => statusMut.mutate('cancelled')} disabled={statusMut.isPending} className="w-full border border-red-400 text-red-600 py-2 rounded text-sm font-medium">Cancel PO</button>
          </>
        )}
      </div>

      {showReceive && <ReceiveModal po={po} onClose={() => setShowReceive(false)} />}
    </div>
  );
}

export default function PurchaseOrdersPage() {
  const [tab, setTab] = useState<Tab>('all');
  const [selectedPO, setSelectedPO] = useState<any>(null);
  const qc = useQueryClient();

  const { data: posPage } = useQuery({
    queryKey: ['inv-pos'],
    queryFn: () => getPurchaseOrders({ page_size: 100 }),
  });

  const { data: reorderItems = [] } = useQuery({
    queryKey: ['inv-reorder'],
    queryFn: getReorderList,
  });

  const generateMut = useMutation({
    mutationFn: generatePurchaseOrders,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inv-pos'] });
      setTab('all');
    },
  });

  const pos = posPage?.items || [];

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-800">Purchase Orders</h1>
      </div>

      <div className="flex gap-2 mb-6 border-b">
        {(['all', 'reorder'] as Tab[]).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${tab === t ? 'border-amber-500 text-amber-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
          >
            {t === 'all' ? 'All Orders' : `Reorder Needed (${(reorderItems as any[]).length})`}
          </button>
        ))}
      </div>

      {tab === 'all' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase">
              <tr>
                <th className="px-4 py-3 text-left">PO #</th>
                <th className="px-4 py-3 text-left">Vendor</th>
                <th className="px-4 py-3 text-left">Order Date</th>
                <th className="px-4 py-3 text-left">Expected</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-right">Total</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {pos.map((po: any) => (
                <tr key={po.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedPO(po)}>
                  <td className="px-4 py-3 font-mono text-xs">#{po.id}</td>
                  <td className="px-4 py-3">Vendor #{po.vendor_id}</td>
                  <td className="px-4 py-3 text-xs text-gray-500">{new Date(po.order_date).toLocaleDateString()}</td>
                  <td className="px-4 py-3 text-xs text-gray-500">{po.expected_delivery ? new Date(po.expected_delivery).toLocaleDateString() : '—'}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_BADGE[po.status] || ''}`}>{po.status}</span>
                  </td>
                  <td className="px-4 py-3 text-right font-semibold">${parseFloat(po.total_amount).toFixed(2)}</td>
                </tr>
              ))}
              {pos.length === 0 && <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">No purchase orders</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'reorder' && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <p className="text-sm text-gray-600">{(reorderItems as any[]).length} item(s) at or below reorder point</p>
            <button
              onClick={() => generateMut.mutate()}
              disabled={generateMut.isPending || (reorderItems as any[]).length === 0}
              className="bg-amber-500 hover:bg-amber-600 disabled:bg-gray-300 text-white px-4 py-2 rounded text-sm font-medium"
            >
              {generateMut.isPending ? 'Generating...' : 'Generate Draft POs'}
            </button>
          </div>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">SKU</th>
                  <th className="px-4 py-3 text-left">Name</th>
                  <th className="px-4 py-3 text-right">Current Qty</th>
                  <th className="px-4 py-3 text-right">Reorder Point</th>
                  <th className="px-4 py-3 text-right">Reorder Qty</th>
                  <th className="px-4 py-3 text-left">Vendor</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {(reorderItems as any[]).map((item: any) => (
                  <tr key={item.id}>
                    <td className="px-4 py-3 font-mono text-xs">{item.sku}</td>
                    <td className="px-4 py-3 font-medium">{item.name}</td>
                    <td className={`px-4 py-3 text-right font-semibold ${parseFloat(item.current_quantity) <= 0 ? 'text-red-600' : 'text-amber-600'}`}>{parseFloat(item.current_quantity).toFixed(1)}</td>
                    <td className="px-4 py-3 text-right text-gray-500">{parseFloat(item.reorder_point).toFixed(1)}</td>
                    <td className="px-4 py-3 text-right">{parseFloat(item.reorder_quantity).toFixed(1)}</td>
                    <td className="px-4 py-3 text-xs text-gray-500">{item.vendor_id ? `#${item.vendor_id}` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {selectedPO && <PODrawer po={selectedPO} onClose={() => setSelectedPO(null)} />}
    </div>
  );
}
