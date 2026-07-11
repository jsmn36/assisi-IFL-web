import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { getItems, getCategories, getAlerts, createItem, createCategory, deleteItem, deleteCategory } from '@/api/inventory';
import { Plus, Package, FolderPlus, Trash2, ChevronRight, MoreHorizontal, Settings2, Search } from 'lucide-react';
import { StockLevelBar } from '../components/StockLevelBar';
import { AlertBadge } from '../components/AlertBadge';

function CategoryTree({ categories, selected, onSelect, onDelete }: any) {
  return (
    <div className="space-y-0.5">
      <button
        onClick={() => onSelect(null)}
        className={`w-full text-left px-3 py-1.5 rounded-lg text-sm font-bold transition-all ${!selected ? 'bg-amber-100 text-amber-950 shadow-sm' : 'text-gray-400 hover:bg-gray-100'}`}
      >
        All Infrastructure
      </button>
      {categories.map((cat: any) => (
        <div key={cat.id} className="group">
          <div className={`flex items-center justify-between px-3 py-1.5 rounded-lg transition-all ${selected === cat.id ? 'bg-amber-100 text-amber-950 shadow-sm' : 'hover:bg-gray-100'}`}>
            <button
              onClick={() => onSelect(cat.id)}
              className="flex-1 text-left text-sm font-medium"
            >
              {cat.name}
            </button>
            <button 
              onClick={(e) => { e.stopPropagation(); if(window.confirm('Delete category?')) onDelete(cat.id); }}
              className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded text-red-500 transition-all"
            >
              <Trash2 className="h-3 w-3" />
            </button>
          </div>
          {cat.children?.length > 0 && (
            <div className="ml-4 border-l border-gray-100 pl-2 mt-0.5">
              <CategoryTree categories={cat.children} selected={selected} onSelect={onSelect} onDelete={onDelete} />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default function StockDashboardPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [search, setSearch] = useState('');
  const [showItemForm, setShowItemForm] = useState(false);
  const [showCatForm, setShowCatForm] = useState(false);
  
  const [newItem, setNewItem] = useState({ name: '', sku: '', unit: 'pcs', unit_cost: '0', reorder_point: '5', reorder_quantity: '10' });
  const [newCat, setNewCat] = useState({ name: '', parent_id: null as number | null });

  const alertStatus = searchParams.get('alert_status') || '';

  const { data: categoriesData = [] } = useQuery({
    queryKey: ['inv-categories'],
    queryFn: getCategories,
  });

  const { data: alerts = [] } = useQuery({
    queryKey: ['inv-alerts'],
    queryFn: getAlerts,
  });

  const { data: itemsPage, isLoading } = useQuery({
    queryKey: ['inv-items', selectedCategory, alertStatus, search],
    queryFn: () => getItems({
      category_id: selectedCategory || undefined,
      alert_status: alertStatus || undefined,
      search: search || undefined,
      page_size: 100,
    }),
  });

  const createItemMut = useMutation({
    mutationFn: createItem,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inv-items'] });
      setShowItemForm(false);
      setNewItem({ name: '', sku: '', unit: 'pcs', unit_cost: '0', reorder_point: '5', reorder_quantity: '10' });
    }
  });

  const createCatMut = useMutation({
    mutationFn: createCategory,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inv-categories'] });
      setShowCatForm(false);
      setNewCat({ name: '', parent_id: null });
    }
  });

  const deleteItemMut = useMutation({
    mutationFn: deleteItem,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['inv-items'] })
  });

  const deleteCatMut = useMutation({
    mutationFn: deleteCategory,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['inv-categories'] })
  });

  const items = itemsPage?.items || [];

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar — category tree */}
      <div className="w-64 shrink-0 border-r bg-white p-6 overflow-y-auto flex flex-col">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Inventory Hub</h3>
          <button onClick={() => setShowCatForm(true)} className="p-1.5 bg-gray-100 rounded-full hover:bg-amber-100 hover:text-amber-600 transition-colors">
            <Plus className="h-4 w-4" />
          </button>
        </div>
        <div className="flex-1">
          <CategoryTree categories={categoriesData} selected={selectedCategory} onSelect={setSelectedCategory} onDelete={(id: any) => deleteCatMut.mutate(id)} />
        </div>
      </div>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Toolbar */}
        <div className="p-6 border-b bg-white flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-black text-gray-900 italic tracking-tighter uppercase">Warehouse</h1>
              <AlertBadge alerts={alerts} />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowItemForm(true)}
                className="bg-amber-500 text-amber-950 px-6 py-2 rounded-xl text-sm font-black flex items-center gap-2 shadow-lg hover:bg-amber-600 transition-all active:scale-95"
              >
                <Plus className="h-4 w-4" /> NEW ITEM
              </button>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search by name, SKU or barcode..."
                className="w-full border-gray-100 bg-gray-50 rounded-xl pl-10 pr-4 py-2 text-sm focus:bg-white focus:ring-amber-500 focus:border-amber-500 transition-all"
              />
            </div>
            <div className="flex bg-gray-100 p-1 rounded-xl">
              {(['', 'low', 'out', 'ok'] as const).map(s => (
                <button
                  key={s || 'all'}
                  onClick={() => setSearchParams(s ? { alert_status: s } : {})}
                  className={`px-4 py-1.5 rounded-lg text-[10px] font-black uppercase transition-all ${
                    alertStatus === s
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-500 hover:text-gray-900'
                  }`}
                >
                  {s === '' ? 'All Items' : s === 'low' ? 'Low' : s === 'out' ? 'Out' : 'Optimal'}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">

        {/* Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs font-semibold text-gray-500 uppercase">
              <tr className="text-gray-400 border-b">
                <th className="px-6 py-4 font-black">Item Identity</th>
                <th className="px-6 py-4 font-black">Unit</th>
                <th className="px-6 py-4 font-black">Quantity</th>
                <th className="px-6 py-4 font-black">Stock Health</th>
                <th className="px-6 py-4 font-black text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {isLoading && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>
              )}
              {!isLoading && items.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">No items found</td></tr>
              )}
              {items.map((item: any) => (
                <tr
                  key={item.id}
                  className="group hover:bg-amber-50 transition-colors cursor-pointer border-b last:border-0"
                  onClick={() => navigate(`/inventory/items/${item.id}`)}
                >
                  <td className="px-6 py-4">
                    <div className="font-bold text-gray-900">{item.name}</div>
                    <div className="text-[10px] text-gray-400 font-mono tracking-tighter uppercase">{item.sku}</div>
                  </td>
                  <td className="px-6 py-4 text-xs font-black text-gray-400 uppercase italic">{item.unit}</td>
                  <td className="px-6 py-4">
                    <div className={`text-lg font-black tabular-nums ${
                      parseFloat(item.current_quantity) <= 0 ? 'text-red-500' :
                      parseFloat(item.current_quantity) <= parseFloat(item.reorder_point) ? 'text-amber-500' :
                      'text-gray-900'
                    }`}>
                      {parseFloat(item.current_quantity).toFixed(1)}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <StockLevelBar
                      current={parseFloat(item.current_quantity)}
                      reorderPoint={parseFloat(item.reorder_point)}
                    />
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                       <button
                         onClick={(e) => { e.stopPropagation(); navigate(`/inventory/items/${item.id}`); }}
                         className="p-2 hover:bg-white rounded-lg text-gray-400 hover:text-amber-500 transition-colors"
                       >
                         <Settings2 className="h-4 w-4" />
                       </button>
                       <button
                         onClick={(e) => { 
                           e.stopPropagation(); 
                           if(window.confirm('Erase this item from records?')) deleteItemMut.mutate(item.id); 
                         }}
                         disabled={deleteItemMut.isPending}
                         className="p-2 hover:bg-white rounded-lg text-gray-400 hover:text-red-500 transition-colors"
                       >
                         <Trash2 className="h-4 w-4" />
                       </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Item Creation Modal */}
      {showItemForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-lg">
            <h2 className="text-xl font-bold mb-4">Create New Inventory Item</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="text-xs font-bold text-gray-500">ITEM NAME</label>
                <input value={newItem.name} onChange={e => setNewItem(f => ({ ...f, name: e.target.value }))} className="w-full border rounded-lg px-3 py-2 mt-1" />
              </div>
              <div>
                <label className="text-xs font-bold text-gray-500">SKU / BARCODE</label>
                <input value={newItem.sku} onChange={e => setNewItem(f => ({ ...f, sku: e.target.value }))} className="w-full border rounded-lg px-3 py-2 mt-1" />
              </div>
              <div>
                <label className="text-xs font-bold text-gray-500">UNIT (pk, kg, l)</label>
                <input value={newItem.unit} onChange={e => setNewItem(f => ({ ...f, unit: e.target.value }))} className="w-full border rounded-lg px-3 py-2 mt-1" />
              </div>
              <div>
                <label className="text-xs font-bold text-gray-500">UNIT COST ($)</label>
                <input type="number" value={newItem.unit_cost} onChange={e => setNewItem(f => ({ ...f, unit_cost: e.target.value }))} className="w-full border rounded-lg px-3 py-2 mt-1" />
              </div>
              <div>
                <label className="text-xs font-bold text-gray-500">REORDER POINT</label>
                <input type="number" value={newItem.reorder_point} onChange={e => setNewItem(f => ({ ...f, reorder_point: e.target.value }))} className="w-full border rounded-lg px-3 py-2 mt-1" />
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button onClick={() => setShowItemForm(false)} className="text-gray-500 font-bold px-4 py-2">CANCEL</button>
              <button 
                onClick={() => createItemMut.mutate({ ...newItem, category_id: selectedCategory, unit_cost: parseFloat(newItem.unit_cost), reorder_point: parseFloat(newItem.reorder_point), reorder_quantity: parseFloat(newItem.reorder_quantity) })}
                className="bg-blue-600 text-white px-6 py-2 rounded-xl font-bold shadow-lg"
              >
                CREATE ITEM
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Category Creation Modal */}
      {showCatForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-sm">
            <h2 className="text-xl font-bold mb-4">New Category</h2>
            <label className="text-xs font-bold text-gray-500">CATEGORY NAME</label>
            <input value={newCat.name} onChange={e => setNewCat(f => ({ ...f, name: e.target.value }))} className="w-full border rounded-lg px-3 py-2 mt-1" />
            
            <div className="mt-6 flex justify-end gap-3">
              <button onClick={() => setShowCatForm(false)} className="text-gray-500 font-bold px-4 py-2">CANCEL</button>
              <button 
                onClick={() => createCatMut.mutate({ name: newCat.name, parent_id: selectedCategory })}
                className="bg-gray-900 text-white px-6 py-2 rounded-xl font-bold shadow-lg"
              >
                CREATE
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  </div>
  );
}
