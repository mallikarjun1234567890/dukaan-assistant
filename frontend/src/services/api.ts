import type {
  AdminShop,
  AdminStats,
  AIChatResponse,
  BillingConfig,
  BillingOrder,
  DashboardData,
  Invoice,
  Product,
  ProductPayload,
  RegisterPayload,
  ReorderItem,
  ShopSettings,
  User,
} from '../types'

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

function readCookie(name: string): string {
  const parts = document.cookie.split(';')
  for (const part of parts) {
    const [key, ...rest] = part.trim().split('=')
    if (key === name) {
      return decodeURIComponent(rest.join('='))
    }
  }
  return ''
}

function errorMessage(payload: unknown, fallback: string): string {
  if (payload && typeof payload === 'object' && 'detail' in payload) {
    const detail = (payload as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail
        .map((item) => (typeof item === 'string' ? item : JSON.stringify(item)))
        .join(' ')
    }
  }
  return fallback
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  const csrf = readCookie('csrf_token')
  if (csrf) {
    headers.set('X-CSRF-Token', csrf)
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: 'include',
    headers,
  })

  if (response.status === 204) {
    return undefined as T
  }

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(response.status, errorMessage(payload, `Request failed (${response.status})`))
  }
  return payload as T
}

export const api = {
  health: () => request<{ status: string }>('/api/health'),
  csrf: () => request<{ csrf_token: string }>('/api/auth/csrf'),
  login: (email: string, password: string) =>
    request<{ user: User; csrf_token: string }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  register: (payload: Omit<RegisterPayload, 'shop_photo' | 'owner_photo'>) =>
    request<{ user: User; csrf_token: string }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  adminLogin: (email: string, password: string) =>
    request<{ user: User; csrf_token: string }>('/api/admin/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  adminStats: () => request<AdminStats>('/api/admin/stats'),
  adminShops: () => request<{ items: AdminShop[] }>('/api/admin/shops'),
  adminLockShop: (shopId: number) =>
    request<AdminShop>(`/api/admin/shops/${shopId}/lock`, { method: 'POST' }),
  adminUnlockShop: (shopId: number) =>
    request<AdminShop>(`/api/admin/shops/${shopId}/unlock`, { method: 'POST' }),
  adminExtendTrial: (shopId: number) =>
    request<AdminShop>(`/api/admin/shops/${shopId}/extend-trial`, { method: 'POST' }),
  adminMarkActive: (shopId: number) =>
    request<AdminShop>(`/api/admin/shops/${shopId}/mark-active`, { method: 'POST' }),
  adminDeleteShop: (shopId: number) =>
    request<{ detail: string }>(`/api/admin/shops/${shopId}`, { method: 'DELETE' }),
  shop: () => request<ShopSettings>('/api/shop'),
  updateShop: (payload: Partial<ShopSettings>) =>
    request<ShopSettings>('/api/shop', { method: 'PUT', body: JSON.stringify(payload) }),
  logout: () => request<{ detail: string }>('/api/auth/logout', { method: 'POST' }),
  me: () => request<User>('/api/auth/me'),
  dashboard: () => request<DashboardData>('/api/dashboard'),
  products: (params?: { search?: string; category?: string; stock_status?: string }) => {
    const query = new URLSearchParams()
    if (params?.search) query.set('search', params.search)
    if (params?.category) query.set('category', params.category)
    if (params?.stock_status) query.set('stock_status', params.stock_status)
    const suffix = query.toString() ? `?${query.toString()}` : ''
    return request<{ items: Product[]; total: number; categories: string[] }>(`/api/products${suffix}`)
  },
  createProduct: (payload: ProductPayload) =>
    request<Product>('/api/products', { method: 'POST', body: JSON.stringify(payload) }),
  updateProduct: (id: number, payload: ProductPayload) =>
    request<Product>(`/api/products/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteProduct: (id: number) => request<void>(`/api/products/${id}`, { method: 'DELETE' }),
  invoices: () => request<{ items: Invoice[] }>('/api/invoices'),
  invoice: (id: number) => request<Invoice>(`/api/invoices/${id}`),
  createInvoice: (items: { product_id: number; quantity: number }[], idempotencyKey: string) =>
    request<Invoice>('/api/invoices', {
      method: 'POST',
      body: JSON.stringify({ items, idempotency_key: idempotencyKey }),
    }),
  reorders: () => request<{ items: ReorderItem[]; rule: string }>('/api/reorders'),
  approveReorder: (id: number) =>
    request<ReorderItem>(`/api/reorders/${id}/approve`, { method: 'POST' }),
  rejectReorder: (id: number) =>
    request<ReorderItem>(`/api/reorders/${id}/reject`, { method: 'POST' }),
  chat: (message: string) =>
    request<AIChatResponse>('/api/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    }),
  upload: (file: File, kind: 'product' | 'shop_logo' | 'avatar', productId?: number) => {
    const body = new FormData()
    body.append('file', file)
    body.append('kind', kind)
    if (productId != null) body.append('product_id', String(productId))
    return request<{ url: string; kind: string }>('/api/uploads', { method: 'POST', body })
  },
  billingConfig: () => request<BillingConfig>('/api/billing/config'),
  createBillingOrder: () => request<BillingOrder>('/api/billing/order', { method: 'POST' }),
  forgotPassword: (email: string) =>
    request<{ detail: string }>('/api/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),
  resetPassword: (token: string, password: string) =>
    request<{ detail: string }>('/api/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, password }),
    }),
  verifyBilling: (payload: {
    razorpay_order_id: string
    razorpay_payment_id: string
    razorpay_signature: string
  }) => request<{ detail: string; plan: string }>('/api/billing/verify', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
}

export function formatINR(value: string | number): string {
  const amount = typeof value === 'number' ? value : Number(value)
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
  }).format(Number.isFinite(amount) ? amount : 0)
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}
