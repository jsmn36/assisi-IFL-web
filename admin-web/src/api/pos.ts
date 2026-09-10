/**
 * POS API client
 */
import client from '@/lib/axiosClient';

const BASE = '/api/v1/pos';

// --- Departments ---
export const getDepartments = () => client.get(`${BASE}/departments`).then(r => r.data);
export const createDepartment = (data: any) => client.post(`${BASE}/departments`, data).then(r => r.data);
export const updateDepartment = (id: number, data: any) => client.put(`${BASE}/departments/${id}`, data).then(r => r.data);
export const deleteDepartment = (id: number) => client.delete(`${BASE}/departments/${id}`).then(r => r.data);

// --- Menu ---
export const getMenuItems = (params?: { category_id?: number; department_id?: number }) =>
  client.get(`${BASE}/menu/items`, { params }).then(r => r.data);
export const createMenuItem = (data: any) => client.post(`${BASE}/menu/items`, data).then(r => r.data);
export const updateMenuItem = (id: number, data: any) => client.patch(`${BASE}/menu/items/${id}`, data).then(r => r.data);
export const deleteMenuItem = (id: number) => client.delete(`${BASE}/menu/items/${id}`).then(r => r.data);
export const getCategories = (deptId: number) => client.get(`${BASE}/departments/${deptId}/categories`).then(r => r.data);
export const createCategory = (data: any) => client.post(`${BASE}/categories`, data).then(r => r.data);
export const updateCategory = (id: number, data: any) => client.put(`${BASE}/categories/${id}`, data).then(r => r.data);
export const deleteCategory = (id: number) => client.delete(`${BASE}/categories/${id}`).then(r => r.data);

// --- Tables ---
export const getTables = (department_id?: number) =>
  client.get(`${BASE}/tables`, { params: { department_id } }).then(r => r.data);
export const updateTable = (id: number, data: any) => client.patch(`${BASE}/tables/${id}`, data).then(r => r.data);

// --- Orders ---
export const getOrders = (params?: { status?: string; department_id?: number }) =>
  client.get(`${BASE}/orders`, { params }).then(r => r.data);
export const getOrder = (id: number) => client.get(`${BASE}/orders/${id}`).then(r => r.data);
export const createOrder = (data: any) => client.post(`${BASE}/orders`, data).then(r => r.data);
export const updateOrder = (id: number, data: any) => client.patch(`${BASE}/orders/${id}`, data).then(r => r.data);
export const addOrderItems = (orderId: number, items: any[]) =>
  client.post(`${BASE}/orders/${orderId}/items`, items).then(r => r.data);
export const voidOrderItem = (orderId: number, itemId: number, reason: string) =>
  client.delete(`${BASE}/orders/${orderId}/items/${itemId}`, { params: { reason } }).then(r => r.data);
export const confirmOrder = (orderId: number) =>
  client.post(`${BASE}/orders/${orderId}/confirm`, {}).then(r => r.data);

// --- KDS ---
export const getKDSTickets = (params?: { department_id?: number; status?: string }) =>
  client.get(`${BASE}/kds/tickets`, { params }).then(r => r.data);
export const updateKDSTicket = (id: number, status: string) =>
  client.patch(`${BASE}/kds/tickets/${id}`, { status }).then(r => r.data);
export const bumpKDSTicket = (id: number) =>
  client.post(`${BASE}/kds/tickets/${id}/bump`, {}).then(r => r.data);

// --- Bills ---
export const createBill = (order_id: number) => client.post(`${BASE}/bills`, { order_id }).then(r => r.data);
export const getBill = (id: number) => client.get(`${BASE}/bills/${id}`).then(r => r.data);
export const payBill = (id: number, data: any) => client.post(`${BASE}/bills/${id}/pay`, data).then(r => r.data);
export const payRoomCharge = (id: number, data: any) =>
  client.post(`${BASE}/bills/${id}/pay-room-charge`, data).then(r => r.data);
export const splitBill = (id: number, data: any) => client.post(`${BASE}/bills/${id}/split`, data).then(r => r.data);
