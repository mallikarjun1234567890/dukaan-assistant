import { Lock, Store } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Toast } from '../components/Toast'
import { useAuth } from '../context/AuthContext'
import { api, formatDate } from '../services/api'
import { startSubscriptionCheckout } from '../services/razorpay'
import type { BillingConfig } from '../types'

export function SubscriptionLockPage() {
  const { user, logout, refresh } = useAuth()
  const [billing, setBilling] = useState<BillingConfig | null>(null)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')
  const [paying, setPaying] = useState(false)

  useEffect(() => {
    api.billingConfig().then(setBilling).catch((err: Error) => setError(err.message))
  }, [])

  const grace = user?.grace_ends_at || billing?.grace_ends_at

  async function subscribe() {
    if (paying) return
    setPaying(true)
    setError('')
    try {
      await startSubscriptionCheckout({
        onSuccess: async () => {
          setError('')
          setToast('Subscription is now active')
          await refresh()
        },
        onError: (message, terminal = true) => {
          setError(message)
          if (terminal) setPaying(false)
        },
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start Razorpay')
      setPaying(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f3f6f5] px-4">
      <div className="w-full max-w-lg rounded-3xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-amber-400 text-[#0b3b36]">
            <Store />
          </div>
          <div>
            <p className="font-bold text-slate-900">Dukaan Assistant</p>
            <p className="text-sm text-slate-500">{user?.shop_name}</p>
          </div>
        </div>
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-50 text-rose-600">
          <Lock />
        </div>
        <h1 className="text-2xl font-bold text-slate-900">Shop locked</h1>
        <p className="mt-2 text-sm text-slate-600">
          Your 30-day trial has ended. Subscribe to keep inventory, invoices, and shop AI.
          {grace
            ? ` Subscribe or data is removed on ${formatDate(grace)}.`
            : ' Subscribe or this shop’s data will be removed after the grace period.'}
        </p>
        <p className="mt-4 rounded-xl bg-teal-50 px-4 py-3 text-sm text-teal-900">
          <strong>₹499/month</strong>
          <span className="text-teal-700">
            {' '}
            · test charge ₹{billing?.amount_rupees ?? 1} · paid access only after server verification
          </span>
        </p>
        {error ? (
          <p className="mt-4 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700" role="alert">
            {error}
          </p>
        ) : null}
        {billing && !billing.enabled ? (
          <p className="mt-4 text-sm text-slate-500">
            Razorpay test keys are not configured, so checkout cannot start yet.
          </p>
        ) : (
          <button
            type="button"
            onClick={() => void subscribe()}
            disabled={paying}
            className="mt-6 w-full rounded-xl bg-teal-700 px-4 py-2.5 font-semibold text-white hover:bg-teal-800 disabled:opacity-60"
          >
            {paying ? 'Waiting for payment…' : 'Subscribe ₹499/month'}
          </button>
        )}
        <button
          type="button"
          onClick={() => void logout()}
          className="mt-3 w-full rounded-xl px-4 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
        >
          Log out
        </button>
      </div>
      {toast ? <Toast message={toast} tone="success" /> : null}
    </div>
  )
}
