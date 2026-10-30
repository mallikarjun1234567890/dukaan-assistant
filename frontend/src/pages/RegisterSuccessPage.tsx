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
  const urlPlan = parsePlanId(searchParams.get('plan'))
  const [error, setError] = useState('')
  const [status, setStatus] = useState<'idle' | 'opening' | 'paid'>('idle')

  if (loading) {
    return <div className="p-8 text-sm text-slate-500">Checking session…</div>
  }
  if (!user) {
    return <Navigate to={urlPlan === 'monthly' ? '/register?plan=monthly' : '/register?plan=trial'} replace />
  }
  if (user.role === 'platform_admin') {
    return <Navigate to="/admin" replace />
  }

  const preference = user.checkout_preference === 'monthly' || urlPlan === 'monthly' ? 'monthly' : 'trial'
  const selected = PLANS[preference]
  const trialEnds = user.trial_ends_at ? formatDate(user.trial_ends_at) : '30 days from registration'
  const alreadyPaid = status === 'paid' || user.plan === 'active'
  const busy = status === 'opening'

  async function startPaid() {
    if (busy || alreadyPaid) return
    setStatus('opening')
    setError('')
    try {
      await startSubscriptionCheckout({
        onSuccess: async () => {
          setError('')
          setStatus('paid')
          await refresh()
        },
        onError: (message, terminal = true) => {
          setError(message)
          if (terminal) setStatus('idle')
        },
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start Razorpay checkout')
      setStatus('idle')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f3f6f5] px-4 py-12">
      <div className="w-full max-w-lg rounded-3xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
        <BrandMark to={SHOP_HOME} />
        <p className="mt-6 text-sm font-semibold uppercase tracking-[0.16em] text-teal-700">Shop ready</p>
        <h1 className="mt-2 text-2xl font-extrabold text-slate-900">{user.shop_name} is set up</h1>
        <p className="mt-3 text-sm text-slate-600">
          Selected plan: <strong>{selected.name}</strong>
          {preference === 'trial' ? ` · ${selected.period}` : ` · ${selected.price}${selected.period}`}
        </p>

        {!alreadyPaid ? (
          <p className="mt-4 rounded-2xl bg-teal-50 px-4 py-3 text-sm text-teal-900">
            The server started a 30-day trial
            {user.trial_ends_at ? ` ending ${trialEnds}` : ''}. Repeated sign-in does not restart those dates.
          </p>
        ) : (
          <p className="mt-4 rounded-2xl bg-teal-50 px-4 py-3 text-sm text-teal-900">
            Payment was verified by the server. The monthly plan is now active for this shop.
          </p>
        )}

        {preference === 'monthly' && !alreadyPaid ? (
          <div className="mt-4 rounded-2xl bg-amber-50 px-4 py-3 text-sm text-amber-950">
            <p className="font-semibold">Payment is still pending</p>
            <p className="mt-1">
              The advertised price is ₹499/month. Test mode charges the server-configured test amount (default ₹1).
              Paid access turns on only after the backend verifies a captured Razorpay payment. Skip checkout to stay
              on the same trial.
            </p>
          </div>
        ) : null}

        {error ? (
          <p className="mt-4 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700" role="alert">
            {error}
          </p>
        ) : null}

        <div className="mt-6 flex flex-col gap-3">
          {preference === 'monthly' && !alreadyPaid ? (
            <button
              type="button"
              onClick={() => void startPaid()}
              disabled={busy}
              className="rounded-xl bg-[#0b3b36] px-4 py-2.5 font-semibold text-white hover:bg-[#0d4640] disabled:opacity-60"
            >
              {status === 'opening' ? 'Waiting for payment…' : 'Pay now'}
            </button>
          ) : null}
          <Link
            to={SHOP_HOME}
            className="rounded-xl bg-teal-700 px-4 py-2.5 text-center font-semibold text-white hover:bg-teal-800"
          >
            {preference === 'monthly' && !alreadyPaid ? 'Skip and use trial' : 'Go to dashboard'}
          </Link>
        </div>
      </div>
    </div>
  )
}
