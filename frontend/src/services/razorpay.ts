import { api } from './api'
import { createRazorpayCheckoutSession } from './razorpaySession'

interface RazorpayCheckout {
  open: () => void
  on: (event: string, handler: (response: { error?: { description?: string } }) => void) => void
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
  onError: (message: string, terminal?: boolean) => void
}): Promise<void> {
  const order = await api.createBillingOrder()
  await loadRazorpay()
  if (!window.Razorpay) throw new Error('Razorpay checkout is unavailable')

  const session = createRazorpayCheckoutSession()

  const checkout = new window.Razorpay({
    key: order.key_id,
    amount: order.amount,
    currency: order.currency,
    order_id: order.order_id,
    name: 'Dukaan Assistant',
    description: '₹499/month plan · charged amount is set by the server',
    handler: async (response: {
      razorpay_order_id: string
      razorpay_payment_id: string
      razorpay_signature: string
    }) => {
      if (!session.beginHandler()) return
      try {
        const verified = await api.verifyBilling(response)
        if (verified.plan !== 'active') {
          session.finishFailure()
          options.onError(
            'Payment was received but paid access is not active yet. Try again or contact support.',
            true,
          )
          return
        }
        session.finishSuccess()
        options.onSuccess(verified.plan)
      } catch (err) {
        session.finishFailure()
        options.onError(err instanceof Error ? err.message : 'Could not verify payment', true)
      }
    },
    modal: {
      ondismiss: () =>
        session.noteDismiss(
          (message) => options.onError(message, true),
          'Checkout was cancelled. Your trial is unchanged.',
        ),
    },
  })
  checkout.on('payment.failed', (response) => {
    session.noteFailedAttempt(
      (message) => options.onError(message, false),
      response.error?.description || 'Payment failed. Your trial is unchanged.',
    )
  })
  checkout.open()
}
