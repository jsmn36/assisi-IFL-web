import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getValuationReport, getMovementSummary, getReorderList } from '@/api/inventory';

type Tab = 'valuation' | 'movement' | 'reorder';

function exportCSV(rows: any[], filename: string) {
  if (!rows.length) return;
  const keys = Object.keys(rows[0]);
  const csv = [keys.join(','), ...rows.map(r => keys.map(k => JSON.stringify(r[k] ?? '')).join(','))].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function InventoryReportsPage() {
  const [tab, setTab] = useState<Tab>('valuation');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const { data: valuation = [] } = useQuery({
    queryKey: ['inv-report-val'],
    queryFn: getValuationReport,
    enabled: tab === 'valuation',
  });

  const { data: movSummary = [] } = useQuery({
    queryKey: ['inv-report-mov', startDate, endDate],
    queryFn: () => getMovementSummary({ start_date: startDate || undefined, end_date: endDate || undefined }),
    enabled: tab === 'movement',
  });

  const { data: reorderItems = [] } = useQuery({
    queryKey: ['inv-reorder'],
    queryFn: getReorderList,
    enabled: tab === 'reorder',
  });

  const totalValue = (valuation as any[]).reduce((s: number, r: any) => s + parseFloat(r.total_value || 0), 0);

  return (
    <div className="p-6">
      <h1 className="text-xl font-bold text-gray-800 mb-6">Inventory Reports</h1>

      <div className="flex gap-2 mb-6 border-b">
        {(['valuation', 'movement', 'reorder'] as Tab[]).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors capitalize ${tab === t ? 'border-amber-500 text-amber-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
          >
            {t === 'valuation' ? 'Valuation' : t === 'movement' ? 'Movement Summary' : 'Reorder List'}
          </button>
        ))}
      </div>

      {tab === 'valuation' && (
        <div>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Category</th>
                  <th className="px-4 py-3 text-right">Items</th>
                  <th className="px-4 py-3 text-right">Total Value</th>
                  <th className="px-4 py-3 text-right">% of Total</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {(valuation as any[]).map((r: any) => (
                  <tr key={r.category} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">{r.category}</td>
                    <td className="px-4 py-3 text-right">{r.item_count}</td>
                    <td className="px-4 py-3 text-right font-semibold">${parseFloat(r.total_value).toFixed(2)}</td>
                    <td className="px-4 py-3 text-right text-gray-500">
                      {totalValue > 0 ? ((parseFloat(r.total_value) / totalValue) * 100).toFixed(1) : '0'}%
                    </td>
                  </tr>
                ))}
                <tr className="bg-gray-50 font-bold">
                  <td className="px-4 py-3">Total</td>
                  <td className="px-4 py-3 text-right">{(valuation as any[]).reduce((s: number, r: any) => s + r.item_count, 0)}</td>
                  <td className="px-4 py-3 text-right">${totalValue.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right">100%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'movement' && (
        <div>
          <div className="flex gap-3 mb-4 items-end">
            <div>
              <label className="text-xs text-gray-500">Start Date</label>
              <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} className="block border rounded px-3 py-1.5 text-sm mt-1" />
            </div>
            <div>
              <label className="text-xs text-gray-500">End Date</label>
              <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} className="block border rounded px-3 py-1.5 text-sm mt-1" />
            </div>
            <button
              onClick={() => exportCSV(movSummary as any[], 'movement-summary.csv')}
              className="px-3 py-1.5 border rounded text-sm text-gray-600 hover:bg-gray-50"
            >
              Export CSV
            </button>
          </div>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Category</th>
                  <th className="px-4 py-3 text-right">Total In</th>
                  <th className="px-4 py-3 text-right">Total Out</th>
                  <th className="px-4 py-3 text-right">Net</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {(movSummary as any[]).map((r: any) => (
                  <tr key={r.category} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">{r.category}</td>
                    <td className="px-4 py-3 text-right text-green-600">+{parseFloat(r.total_in).toFixed(2)}</td>
                    <td className="px-4 py-3 text-right text-red-600">-{parseFloat(r.total_out).toFixed(2)}</td>
                    <td className={`px-4 py-3 text-right font-semibold ${parseFloat(r.net) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {parseFloat(r.net) >= 0 ? '+' : ''}{parseFloat(r.net).toFixed(2)}
                    </td>
                  </tr>
                ))}
                {(movSummary as any[]).length === 0 && <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400">No movement data</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'reorder' && (
        <div>
          <div className="flex justify-end mb-4">
            <button
              onClick={() => exportCSV(reorderItems as any[], 'reorder-list.csv')}
              className="px-3 py-1.5 border rounded text-sm text-gray-600 hover:bg-gray-50"
            >
              Export CSV
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
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs">{item.sku}</td>
                    <td className="px-4 py-3 font-medium">{item.name}</td>
                    <td className={`px-4 py-3 text-right font-semibold ${parseFloat(item.current_quantity) <= 0 ? 'text-red-600' : 'text-amber-600'}`}>
                      {parseFloat(item.current_quantity).toFixed(1)}
                    </td>
                    <td className="px-4 py-3 text-right">{parseFloat(item.reorder_point).toFixed(1)}</td>
                    <td className="px-4 py-3 text-right">{parseFloat(item.reorder_quantity).toFixed(1)}</td>
                    <td className="px-4 py-3 text-xs text-gray-500">{item.vendor_id ? `#${item.vendor_id}` : '—'}</td>
                  </tr>
                ))}
                {(reorderItems as any[]).length === 0 && <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">All items above reorder point</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
