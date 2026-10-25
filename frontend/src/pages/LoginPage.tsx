import { Store } from 'lucide-react'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ApiError } from '../services/api'

export function LoginPage() {
  const { user, loading, login } = useAuth()
  const [email, setEmail] = useState('owner@dukaan.local')
  const [password, setPassword] = useState('Demo@12345')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!loading && user) {
    if (user.role === 'platform_admin') {
      return <Navigate to="/admin" replace />
    }
    return <Navigate to="/app" replace />
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(email, password)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to sign in. Check that the API is running.')
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
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal-200">Retail MVP</p>
          <h1 className="mt-4 max-w-md text-4xl font-extrabold leading-tight">
            Run inventory, invoices, and restocking from one counter.
          </h1>
          <p className="mt-5 max-w-md text-teal-100">
            Built for kirana stores, stationery shops, and small supermarkets. Stock, sales, and AI advice stay
            grounded in your shop data.
          </p>
        </div>
        <p className="text-sm text-teal-200">Hackathon-ready MVP · SQLite · FastAPI · Gemini</p>
      </section>

      <section className="flex items-center justify-center px-4 py-12">
        <form onSubmit={onSubmit} className="w-full max-w-md rounded-3xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
          <div className="mb-6 lg:hidden">
            <p className="text-lg font-bold text-teal-800">Dukaan Assistant</p>
          </div>
          <h2 className="text-2xl font-bold text-slate-900">Sign in</h2>
          <p className="mt-2 text-sm text-slate-500">Sign in to your shop, or create a new one for free.</p>

          <label className="mt-6 block text-sm font-medium text-slate-700" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none ring-teal-700 focus:ring-2"
          />

          <label className="mt-4 block text-sm font-medium text-slate-700" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none ring-teal-700 focus:ring-2"
          />

          <p className="mt-2 text-right text-sm">
            <Link to="/forgot-password" className="font-medium text-teal-700 hover:underline">
              Forgot password?
            </Link>
          </p>

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
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>

          <p className="mt-4 text-center text-sm text-slate-500">
            New shop?{' '}
            <Link to="/register?plan=trial" className="font-semibold text-teal-700 hover:underline">
              Start free trial
            </Link>
          </p>
          <div className="mt-4 rounded-xl bg-slate-50 px-4 py-3 text-xs text-slate-500">
            Demo login: <span className="font-semibold text-slate-700">owner@dukaan.local</span> /
            <span className="font-semibold text-slate-700"> Demo@12345</span>
            <span className="mt-1 block">
              <Link to="/admin/login" className="font-medium text-teal-700 hover:underline">
                Platform admin
              </Link>
            </span>
          </div>
        </form>
      </section>
    </div>
  )
}
