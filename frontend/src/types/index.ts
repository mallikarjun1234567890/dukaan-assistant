export type StockStatus = 'out' | 'low' | 'healthy'

export interface User {
  id: number
  email: string
  role: string
  shop_id: number | null
  shop_name: string
  owner_name?: string
  avatar_url?: string
  plan?: string
  shop_locked?: boolean
  trial_ends_at?: string | null
  grace_ends_at?: string | null
  plan_expires_at?: string | null
  paid_at?: string | null
}

export interface ShopSettings {
  shop_id: number
  name: string
  phone: string
  timezone: string
  opens_at: string
  closes_at: string
  weekly_off: string
  logo_url: string
  plan?: string
  trial_started_at?: string | null
  trial_ends_at?: string | null
  grace_ends_at?: string | null
  plan_expires_at?: string | null
  paid_at?: string | null
  shop_locked?: boolean
  local_time: string
  weekday: string
  is_open: boolean
}

export interface Product {
  id: number
  shop_id: number
  name: string
  sku: string
  category: string
  selling_price: string
  purchase_cost: string
  selling_price_paise: number
  purchase_cost_paise: number
  stock_quantity: number
  minimum_stock: number
  supplier_name: string
  is_low_stock: boolean
  stock_status: StockStatus
  image_url?: string
  created_at: string
  updated_at: string
}

export interface ProductPayload {
  name: string
  sku: string
  category: string
  selling_price: string
  purchase_cost: string
  stock_quantity: number
  minimum_stock: number
  supplier_name: string
}

export interface InvoiceItem {
  id: number
  product_id: number | null
  product_name: string
  quantity: number
  unit_price: string
  line_total: string
}

export interface Invoice {
  id: number
  shop_id: number
  invoice_number: string
  subtotal: string
  total: string
  subtotal_paise: number
  total_paise: number
  status: string
  created_at: string
  items: InvoiceItem[]
}

export interface DashboardData {
  shop_name: string
  local_time?: string
  weekday?: string
  is_open?: boolean
  opens_at?: string
  closes_at?: string
  weekly_off?: string
  product_count: number
  inventory_value: string
  inventory_value_paise: number
  low_stock_count: number
  out_of_stock_count: number
  today_sales: string
  today_sales_paise: number
  today_invoice_count: number
  recent_invoices: {
    id: number
    invoice_number: string
    total: string
    status: string
    created_at: string
    item_count: number
  }[]
  stock_levels: {
    name: string
    stock_quantity: number
    minimum_stock: number
    status: string
  }[]
  stock_summary: {
    healthy: number
    low: number
    out: number
  }
}

export interface ReorderItem {
  id: number
  product_id: number
  product_name: string
  sku: string
  current_stock: number
  minimum_stock: number
  suggested_quantity: number
  supplier_name: string
  estimated_cost: string
  estimated_cost_paise: number
  status: string
  created_at: string
  updated_at: string
}

export interface AIChatResponse {
  reply: string
  sources: string[]
  model: string
  provider?: string
}

export interface BillingConfig {
  enabled: boolean
  key_id: string
  plan: string
  amount_rupees: number
  list_price_rupees?: number
  trial_ends_at?: string | null
  grace_ends_at?: string | null
  plan_expires_at?: string | null
  paid_at?: string | null
  shop_locked?: boolean
}

export interface AdminStats {
  total_shops: number
  trial_count: number
  active_count: number
  expired_count: number
  successful_pays: number
  test_revenue_rupees: number
  list_revenue_rupees: number
  list_price_rupees: number
}

export interface AdminShop {
  id: number
  name: string
  owner_email: string
  phone: string
  plan: string
  trial_ends_at: string | null
  grace_ends_at: string | null
  plan_expires_at: string | null
  paid_at: string | null
  created_at: string
}

export interface RegisterPayload {
  email: string
  password: string
  shop_name: string
  owner_name: string
  phone: string
  shop_photo?: File | null
  owner_photo?: File | null
}

export interface BillingOrder {
  order_id: string
  amount: number
  currency: string
  key_id: string
}
