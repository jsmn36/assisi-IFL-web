/**
 * Inventory Terminal — Quick stock adjustment view
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getItems, recordMovement } from '@/api/inventory';
import { Search, Plus, Minus, Package, Clock, ArrowLeft, X } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function InventoryTerminal() {
  const [search, setSearch] = useState('');
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [adjustmentValue, setAdjustmentValue] = useState(1);
  const qc = useQueryClient();

  const { data: itemsPage, isLoading } = useQuery({
    queryKey: ['inv-items-terminal', search],
    queryFn: () => getItems({ search: search || undefined, page_size: 10 }),
    enabled: true
  });

  const movMut = useMutation({
    mutationFn: (data: any) => recordMovement(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inv-items-terminal'] });
      setSelectedItem(null);
      setAdjustmentValue(1);
    }
  });

  const items = itemsPage?.items || [];

  return (
    <div className="max-w-4xl mx-auto p-4 flex flex-col h-screen md:h-auto">
      <div className="flex items-center gap-4 mb-2">
        <Link to="/dashboard" className="text-gray-400 hover:text-gray-900 flex items-center gap-1 text-sm font-bold">
          <ArrowLeft className="h-4 w-4" />
          BACK TO PMS
        </Link>
      </div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-black text-gray-900 uppercase italic">Stock Terminal</h1>
        <div className="bg-amber-100 text-amber-800 px-3 py-1 rounded-full text-xs font-bold animate-pulse">LIVE SYNC</div>
      </div>

      {/* Search Section */}
      <div className="relative mb-6">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-6 w-6 text-gray-400" />
        </div>
        <input
          type="text"
          className="block w-full pl-12 pr-4 py-4 bg-white border-2 border-gray-100 rounded-2xl text-xl font-bold focus:border-amber-500 focus:ring-0 transition-all shadow-sm"
          placeholder="Scan barcode or type name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-20 md:pb-0">
        {/* Results / Adjustment Selection */}
        <div className="space-y-4">
          <h2 className="text-sm font-bold text-gray-500 uppercase tracking-widest px-2">Results</h2>
          {isLoading && <div className="text-center py-10 text-gray-400 font-medium">Scanning warehouse...</div>}
          <div className="grid grid-cols-1 gap-3 overflow-y-auto max-h-[500px] pr-2">
            {items.map((item: any) => (
              <button
                key={item.id}
                onClick={() => setSelectedItem(item)}
                className={`p-4 rounded-2xl border-2 transition-all flex justify-between items-center ${
                  selectedItem?.id === item.id 
                  ? 'border-amber-500 bg-amber-50 shadow-md transform scale-[1.02]' 
                  : 'border-white bg-white hover:border-gray-200'
                }`}
              >
                <div className="text-left">
                  <div className="text-lg font-bold text-gray-900">{item.name}</div>
                  <div className="text-xs text-gray-500 font-mono italic">{item.sku}</div>
                </div>
                <div className="text-right">
                  <div className="text-xl font-black text-amber-600">{parseFloat(item.current_quantity).toFixed(1)}</div>
                  <div className="text-[10px] text-gray-400 uppercase font-black">{item.unit}</div>
                </div>
              </button>
            ))}
            {!isLoading && items.length === 0 && (
              <div className="bg-white rounded-2xl p-10 text-center text-gray-400 border-2 border-dashed border-gray-100">
                <Package className="h-12 w-12 mx-auto mb-2 opacity-10" />
                No matching inventory found.
              </div>
            )}
          </div>
        </div>

        {/* Quick Action Panel (Hidden on mobile, uses slide-up) */}
        <div className={`
          fixed inset-x-0 bottom-0 z-40 md:relative md:inset-auto md:w-auto p-6 md:p-6 bg-gray-900 rounded-t-[32px] md:rounded-[32px] text-white shadow-2xl transition-transform duration-300 transform
          ${selectedItem ? 'translate-y-0' : 'translate-y-full md:translate-y-0'}
        `}>
          {!selectedItem ? (
            <div className="hidden md:flex flex-col items-center justify-center h-full text-center p-8 opacity-40">
              <Plus className="h-16 w-16 mb-4" />
              <h2 className="text-xl font-bold">Select an item above to start stock entry</h2>
            </div>
          ) : (
            <div className="flex flex-col justify-between h-full">
              <div>
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-xs font-black text-amber-500 uppercase tracking-[0.2em]">Quick Adjustment</h2>
                    <h3 className="text-2xl font-bold truncate max-w-[200px]">{selectedItem.name}</h3>
                    <p className="text-[10px] text-gray-500 uppercase font-black">{selectedItem.sku}</p>
                  </div>
                  <button onClick={() => setSelectedItem(null)} className="p-2 bg-gray-800 rounded-full hover:text-white transition-colors">
                    <X className="h-5 w-5" />
                  </button>
                </div>

                <div className="flex items-center justify-center gap-8 my-6 md:my-10">
                  <button 
                    onClick={() => setAdjustmentValue(v => Math.max(0.1, v - 1))}
                    className="w-20 h-20 rounded-full bg-gray-800 flex items-center justify-center text-white hover:bg-red-600 transition-all font-black text-4xl shadow-xl"
                  >
                    -
                  </button>
                  <div className="text-center min-w-[120px]">
                    <div className="text-6xl font-black text-amber-500 tabular-nums">{adjustmentValue}</div>
                    <div className="text-xs text-gray-400 uppercase font-bold mt-2">Adjust Qty</div>
                  </div>
                  <button 
                    onClick={() => setAdjustmentValue(v => v + 1)}
                    className="w-20 h-20 rounded-full bg-gray-800 flex items-center justify-center text-white hover:bg-green-600 transition-all font-black text-4xl shadow-xl"
                  >
                    +
                  </button>
                </div>
              </div>

              <div className="space-y-4">
                <button 
                  onClick={() => movMut.mutate({ item_id: selectedItem.id, movement_type: 'adjustment', quantity_delta: adjustmentValue, notes: 'Terminal quick-add' })}
                  disabled={movMut.isPending}
                  className="w-full bg-amber-500 hover:bg-amber-600 py-6 rounded-3xl text-2xl font-black transition-all shadow-2xl active:scale-95 text-gray-900 flex items-center justify-center gap-3"
                >
                  {movMut.isPending ? 'SYNCING...' : <><Plus /> CONFIRM IN</>}
                </button>
                <div className="flex gap-3">
                  <button 
                    onClick={() => movMut.mutate({ item_id: selectedItem.id, movement_type: 'waste', quantity_delta: -adjustmentValue, notes: 'Terminal quick-subtract' })}
                    disabled={movMut.isPending}
                    className="flex-1 bg-gray-800 hover:bg-red-600 py-4 rounded-2xl text-xs font-black transition-all text-gray-400 hover:text-white"
                  >
                    REMOVE STOCK (-)
                  </button>
                  <button 
                    onClick={() => setSelectedItem(null)}
                    className="flex-1 bg-gray-800 py-4 rounded-2xl text-xs font-black transition-all text-gray-400 md:hidden"
                  >
                    CANCEL
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
