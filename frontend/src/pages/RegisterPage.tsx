import { Camera, Image, Lock, Mail, Phone, Store, User } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import type { ChangeEvent, FormEvent, ReactNode } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { isExactPlanId, parsePlanId, PLANS, SHOP_HOME } from '../lib/plans'
import { ApiError } from '../services/api'

function FieldLabel({
  htmlFor,
  icon,
  children,
}: {
  htmlFor: string
  icon: ReactNode
  children: ReactNode
}) {
  return (
    <label className="mt-4 flex items-center gap-2 text-sm font-medium text-slate-700" htmlFor={htmlFor}>
      <span className="text-teal-700">{icon}</span>
      {children}
    </label>
  )
}

export function RegisterPage() {
  const { user, loading, register } = useAuth()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const plan = parsePlanId(searchParams.get('plan'))
  const selected = PLANS[plan]
  const [shopName, setShopName] = useState('')
  const [ownerName, setOwnerName] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [shopPhoto, setShopPhoto] = useState<File | null>(null)
  const [ownerPhoto, setOwnerPhoto] = useState<File | null>(null)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const finishingRef = useRef(false)

  useEffect(() => {
    if (!isExactPlanId(searchParams.get('plan'))) {
      setSearchParams({ plan }, { replace: true })
    }
  }, [plan, searchParams, setSearchParams])

  if (loading) {
    return <div className="p-8 text-sm text-slate-500">Checking session…</div>
  }

  if (user && !finishingRef.current) {
    if (user.role === 'platform_admin') {
      return <Navigate to="/admin" replace />
    }
    return <Navigate to={SHOP_HOME} replace />
  }

  function onFile(setter: (file: File | null) => void, event: ChangeEvent<HTMLInputElement>) {
    setter(event.target.files?.[0] ?? null)
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    finishingRef.current = true
    try {
      await register({
        email,
        password,
        shop_name: shopName,
        owner_name: ownerName,
        phone,
        shop_photo: shopPhoto,
        owner_photo: ownerPhoto,
      })
      navigate(`/register/success?plan=${plan}`, { replace: true })
    } catch (err) {
      finishingRef.current = false
      setError(err instanceof ApiError ? err.message : 'Unable to create the shop. Check that the API is running.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <section className="relative hidden overflow-hidden bg-[#0b3b36] px-12 py-16 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-amber-400 text-[#0b3b36]">
            <Store />
          </div>
          <span className="text-lg font-bold">Dukaan Assistant</span>
        </div>
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal-200">Create your shop</p>
          <h1 className="mt-4 max-w-md text-4xl font-extrabold leading-tight">
            {plan === 'trial' ? 'Start the 30-day trial after you register.' : 'Register, then complete checkout.'}
          </h1>
          <p className="mt-5 max-w-md text-teal-100">
            {selected.summary} The plan you picked stays selected if the form has an error.
          </p>
        </div>
        <p className="text-sm text-teal-200">Each signup creates a separate shop. Data stays isolated.</p>
      </section>

      <section className="flex items-center justify-center px-4 py-12">
        <form onSubmit={onSubmit} className="w-full max-w-md rounded-3xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
          <h2 className="text-2xl font-bold text-slate-900">Register</h2>
          <p className="mt-2 text-sm text-slate-500">
            Enter the shop and owner details. The selected plan is shown below and is kept in the page URL.
          </p>

          <div
            className={`mt-5 rounded-2xl px-4 py-3 text-sm ring-1 ${
              plan === 'monthly' ? 'bg-[#0b3b36] text-white ring-teal-900' : 'bg-teal-50 text-teal-950 ring-teal-100'
            }`}
          >
            <p className="font-semibold">{selected.name}</p>
            <p className={plan === 'monthly' ? 'mt-1 text-teal-100' : 'mt-1 text-teal-800'}>
              {plan === 'trial'
                ? `${selected.price} · ${selected.period} of full shop access`
                : `${selected.price}${selected.period} advertised · ₹1 Razorpay test charge`}
            </p>
            <p className={`mt-2 text-xs ${plan === 'monthly' ? 'text-teal-100/80' : 'text-teal-800/80'}`}>
              <Link to="/#pricing" className="font-semibold underline-offset-2 hover:underline">
                Change plan
              </Link>
            </p>
          </div>

          <FieldLabel htmlFor="shop" icon={<Store size={16} />}>
            Shop name
          </FieldLabel>
          <input
            id="shop"
            required
            minLength={2}
            value={shopName}
            onChange={(event) => setShopName(event.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none ring-teal-700 focus:ring-2"
          />

          <FieldLabel htmlFor="owner" icon={<User size={16} />}>
            Owner name
          </FieldLabel>
          <input
            id="owner"
            required
            minLength={1}
            value={ownerName}
            onChange={(event) => setOwnerName(event.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none ring-teal-700 focus:ring-2"
          />

          <FieldLabel htmlFor="phone" icon={<Phone size={16} />}>
            Phone
          </FieldLabel>
          <input
            id="phone"
            type="tel"
            required
            minLength={8}
            maxLength={30}
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none ring-teal-700 focus:ring-2"
          />

          <FieldLabel htmlFor="email" icon={<Mail size={16} />}>
            Email
          </FieldLabel>
          <input
            id="email"
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none ring-teal-700 focus:ring-2"
          />

          <FieldLabel htmlFor="password" icon={<Lock size={16} />}>
            Password (8+ characters)
          </FieldLabel>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none ring-teal-700 focus:ring-2"
          />

          <FieldLabel htmlFor="shop-photo" icon={<Image size={16} />}>
            Shop photo <span className="font-normal text-slate-400">(optional)</span>
          </FieldLabel>
          <input
            id="shop-photo"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(event) => onFile(setShopPhoto, event)}
            className="mt-1 w-full text-sm text-slate-600"
          />

          <FieldLabel htmlFor="owner-photo" icon={<Camera size={16} />}>
            Owner photo <span className="font-normal text-slate-400">(optional)</span>
          </FieldLabel>
          <input
            id="owner-photo"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(event) => onFile(setOwnerPhoto, event)}
            className="mt-1 w-full text-sm text-slate-600"
          />

          {error ? (
            <p className="mt-4 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700" role="alert">
              {error}
            </p>
          ) : null}

          <button
            type="submit"
            disabled={submitting || loading}
            className="mt-6 w-full rounded-xl bg-teal-700 px-4 py-2.5 font-semibold text-white hover:bg-teal-800 disabled:opacity-60"
          >
            {submitting ? 'Creating shop…' : plan === 'trial' ? 'Create shop and start trial' : 'Create shop and continue'}
          </button>

          <p className="mt-4 text-center text-sm text-slate-500">
            Already have an account?{' '}
            <Link to="/login" className="font-semibold text-teal-700 hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </section>
    </div>
  )
}
