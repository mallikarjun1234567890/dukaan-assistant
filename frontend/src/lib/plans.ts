export const PLAN_IDS = ['trial', 'monthly'] as const

export type PlanId = (typeof PLAN_IDS)[number]

export const SHOP_HOME = '/app'

const FEATURES = [
  'Inventory with search, categories, and stock status',
  'Invoice generation with print-ready history',
  'Low-stock alerts on the dashboard',
  'Reorder recommendations with approve or reject',
  'Sales dashboard with confirmed totals',
  'AI shop assistant grounded in your shop data',
  'Shop settings, hours, and image uploads',
] as const

export const PLANS: Record<
  PlanId,
  {
    id: PlanId
    name: string
    price: string
    period: string
    summary: string
    cta: string
    features: readonly string[]
    notes: readonly string[]
  }
> = {
  trial: {
    id: 'trial',
    name: 'Free trial',
    price: '₹0',
    period: '30 days',
    summary: 'Full shop access for 30 days. Dates are set by the server when you register.',
    cta: 'Start free trial',
    features: FEATURES,
    notes: [
      'One shop and one owner account',
      'Welcome email is sent on a best-effort basis',
      'After 30 days the shop locks until you subscribe',
    ],
  },
  monthly: {
    id: 'monthly',
    name: 'Monthly plan',
    price: '₹499',
    period: '/month',
    summary: 'Same shop tools, billed as a monthly plan after checkout.',
    cta: 'Subscribe now',
    features: FEATURES,
    notes: [
      'Checkout uses Razorpay in test mode',
      'The test charge is ₹1, not a live ₹499 payment',
      'Paid access is activated only after the server verifies the payment',
      'Automatic recurring billing is not implemented yet',
    ],
  },
}

export function parsePlanId(value: string | null | undefined): PlanId {
  if (value === 'monthly' || value === 'paid' || value === 'subscribe') {
    return 'monthly'
  }
  return 'trial'
}

export function isExactPlanId(value: string | null | undefined): value is PlanId {
  return value === 'trial' || value === 'monthly'
}

export function registerPath(plan: PlanId): string {
  return `/register?plan=${plan}`
}
