/**
 * Inventory API client
 */
import client from '@/lib/axiosClient';

const BASE = '/api/v1/inventory';

// ── Vendors ──
export const getVendors = () => client.get(`${BASE}/vendors`).then(r => r.data);
export const createVendor = (data: any) => client.post(`${BASE}/vendors`, data).then(r => r.data);
export const updateVendor = (id: number, data: any) => client.put(`${BASE}/vendors/${id}`, data).then(r => r.data);

// ── Categories ──
export const getCategories = () => client.get(`${BASE}/categories`).then(r => r.data);
export const createCategory = (data: any) => client.post(`${BASE}/categories`, data).then(r => r.data);
export const deleteCategory = (id: number) => client.delete(`${BASE}/categories/${id}`).then(r => r.data);

// ── Items ──
export const getItems = (params?: any) => client.get(`${BASE}/items`, { params }).then(r => r.data);
export const createItem = (data: any) => client.post(`${BASE}/items`, data).then(r => r.data);
export const updateItem = (id: number, data: any) => client.put(`${BASE}/items/${id}`, data).then(r => r.data);
export const deleteItem = (id: number) => client.delete(`${BASE}/items/${id}`).then(r => r.data);
export const getItemMovements = (id: number, params?: any) => client.get(`${BASE}/items/${id}/movements`, { params }).then(r => r.data);

// ── Recipes ──
export const getRecipe = (pos_menu_item_id: number) => client.get(`${BASE}/recipes/${pos_menu_item_id}`).then(r => r.data);
export const addRecipeIngredient = (data: any) => client.post(`${BASE}/recipes`, data).then(r => r.data);
export const updateRecipeIngredient = (ingredient_id: number, data: any) => client.put(`${BASE}/recipes/ingredient/${ingredient_id}`, data).then(r => r.data);
export const deleteRecipeIngredient = (ingredient_id: number) => client.delete(`${BASE}/recipes/ingredient/${ingredient_id}`).then(r => r.data);

// ── Movements ──
export const recordMovement = (data: any) => client.post(`${BASE}/movements`, data).then(r => r.data);
export const getMovements = (params?: any) => client.get(`${BASE}/movements`, { params }).then(r => r.data);

// ── Purchase Orders ──
export const getPurchaseOrders = (params?: any) => client.get(`${BASE}/purchase-orders`, { params }).then(r => r.data);
export const createPurchaseOrder = (data: any) => client.post(`${BASE}/purchase-orders`, data).then(r => r.data);
export const getPurchaseOrder = (id: number) => client.get(`${BASE}/purchase-orders/${id}`).then(r => r.data);
export const updatePOStatus = (id: number, status: string) => client.patch(`${BASE}/purchase-orders/${id}/status`, { status }).then(r => r.data);
export const receivePurchaseOrder = (id: number, data: any) => client.post(`${BASE}/purchase-orders/${id}/receive`, data).then(r => r.data);
export const generatePurchaseOrders = () => client.post(`${BASE}/purchase-orders/generate`, {}).then(r => r.data);

// ── Alerts ──
export const getAlerts = (params?: any) => client.get(`${BASE}/alerts`, { params }).then(r => r.data);
export const acknowledgeAlert = (id: number, acknowledged_by: string) => client.patch(`${BASE}/alerts/${id}/acknowledge`, { acknowledged_by }).then(r => r.data);

// ── Reports ──
export const getValuationReport = () => client.get(`${BASE}/reports/valuation`).then(r => r.data);
export const getMovementSummary = (params?: any) => client.get(`${BASE}/reports/movement-summary`, { params }).then(r => r.data);
export const getReorderList = () => client.get(`${BASE}/reports/reorder-list`).then(r => r.data);
