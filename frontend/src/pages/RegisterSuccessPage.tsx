import { useState } from 'react'
import { Link, Navigate, useSearchParams } from 'react-router-dom'
import { BrandMark } from '../components/BrandMark'
import { useAuth } from '../context/AuthContext'
import { parsePlanId, PLANS, SHOP_HOME } from '../lib/plans'
import { formatDate } from '../services/api'
import { startSubscriptionCheckout } from '../services/razorpay'

export function RegisterSuccessPage() {
  const { user, loading, refresh } = useAuth()
  const [searchParams] = useSearchParams()
  const plan = parsePlanId(searchParams.get('plan'))
  const selected = PLANS[plan]
  const [error, setError] = useState('')
  const [paying, setPaying] = useState(false)
  const [paid, setPaid] = useState(false)

  if (loading) {
    return <div className="p-8 text-sm text-slate-500">Checking session…</div>
  }
  if (!user) {
    return <Navigate to={plan === 'monthly' ? '/register?plan=monthly' : '/register?plan=trial'} replace />
  }
  if (user.role === 'platform_admin') {
    return <Navigate to="/admin" replace />
  }

  async function startPaid() {
    setPaying(true)
    setError('')
    try {
      await startSubscriptionCheckout({
        onSuccess: async () => {
          setPaid(true)
          await refresh()
        },
        onError: (message) => setError(message),
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start Razorpay checkout')
    } finally {
      setPaying(false)
    }
  }

  const trialEnds = user.trial_ends_at ? formatDate(user.trial_ends_at) : '30 days from registration'
  const alreadyPaid = paid || user.plan === 'active'

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f3f6f5] px-4 py-12">
      <div className="w-full max-w-lg rounded-3xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
        <BrandMark to={SHOP_HOME} />
        <p className="mt-6 text-sm font-semibold uppercase tracking-[0.16em] text-teal-700">Shop ready</p>
        <h1 className="mt-2 text-2xl font-extrabold text-slate-900">{user.shop_name} is set up</h1>
        <p className="mt-3 text-sm text-slate-600">
          Selected plan: <strong>{selected.name}</strong>
          {plan === 'trial' ? ` · ${selected.period}` : ` · ${selected.price}${selected.period}`}
        </p>

        {plan === 'trial' || !alreadyPaid ? (
          <p className="mt-4 rounded-2xl bg-teal-50 px-4 py-3 text-sm text-teal-900">
            The server started a 30-day trial
            {user.trial_ends_at ? ` ending ${trialEnds}` : ''}. Repeated sign-in does not restart those dates.
          </p>
        ) : (
          <p className="mt-4 rounded-2xl bg-teal-50 px-4 py-3 text-sm text-teal-900">
            Payment was verified. The monthly plan is now active for this shop.
          </p>
        )}

        {plan === 'monthly' && !alreadyPaid ? (
          <div className="mt-4 rounded-2xl bg-amber-50 px-4 py-3 text-sm text-amber-950">
            <p className="font-semibold">Payment is still pending</p>
            <p className="mt-1">
              The advertised price is ₹499/month. Checkout uses Razorpay test mode and charges ₹1. Paid access
              turns on only after the backend verifies the signature. Until then this shop remains on the trial.
            </p>
          </div>
        ) : null}

        {error ? (
          <p className="mt-4 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700" role="alert">
            {error}
          </p>
        ) : null}

        <div className="mt-6 flex flex-col gap-3">
          {plan === 'monthly' && !alreadyPaid ? (
            <button
              type="button"
              onClick={() => void startPaid()}
              disabled={paying}
              className="rounded-xl bg-[#0b3b36] px-4 py-2.5 font-semibold text-white hover:bg-[#0d4640] disabled:opacity-60"
            >
              {paying ? 'Opening checkout…' : 'Continue to test checkout'}
            </button>
          ) : null}
          <Link
            to={SHOP_HOME}
            className="rounded-xl bg-teal-700 px-4 py-2.5 text-center font-semibold text-white hover:bg-teal-800"
          >
            Go to dashboard
          </Link>
        </div>
      </div>
    </div>
  )
}
