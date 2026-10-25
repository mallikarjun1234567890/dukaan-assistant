import { api } from './api'

interface RazorpayCheckout {
  open: () => void
}

interface RazorpayCtor {
  new (options: Record<string, unknown>): RazorpayCheckout
}

declare global {
  interface Window {
    Razorpay?: RazorpayCtor
  }
}

function loadRazorpay(): Promise<void> {
  if (window.Razorpay) return Promise.resolve()
  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Could not load Razorpay checkout'))
    document.body.appendChild(script)
  })
}

export async function startSubscriptionCheckout(options: {
  onSuccess: (plan: string) => void
  onError: (message: string) => void
}): Promise<void> {
  const order = await api.createBillingOrder()
  await loadRazorpay()
  if (!window.Razorpay) throw new Error('Razorpay checkout is unavailable')
  const checkout = new window.Razorpay({
    key: order.key_id,
    amount: order.amount,
    currency: order.currency,
    order_id: order.order_id,
    name: 'Dukaan Assistant',
    description: '₹499/month plan · test charge ₹1',
    handler: async (response: {
      razorpay_order_id: string
      razorpay_payment_id: string
      razorpay_signature: string
    }) => {
      try {
        const verified = await api.verifyBilling(response)
        options.onSuccess(verified.plan)
      } catch (err) {
        options.onError(err instanceof Error ? err.message : 'Could not verify payment')
      }
    },
  })
  checkout.open()
}
