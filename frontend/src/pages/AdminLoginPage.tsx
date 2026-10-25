import { Shield, Store } from 'lucide-react'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ApiError } from '../services/api'

export function AdminLoginPage() {
  const { user, loading, adminLogin } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
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
      await adminLogin(email, password)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to sign in as admin.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <section className="relative hidden overflow-hidden bg-[#0b3b36] px-12 py-16 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-amber-400 text-[#0b3b36]">
            <Shield />
          </div>
          <span className="text-lg font-bold">Dukaan platform</span>
        </div>
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal-200">Application owner</p>
          <h1 className="mt-4 max-w-md text-4xl font-extrabold leading-tight">
            See every shop. Lock, extend, or remove a tenant.
          </h1>
        </div>
        <p className="text-sm text-teal-200">This is not a shop login. Shop owners stay on the storefront.</p>
      </section>

      <section className="flex items-center justify-center px-4 py-12">
        <form onSubmit={onSubmit} className="w-full max-w-md rounded-3xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
          <div className="mb-6 flex items-center gap-2 text-teal-800 lg:hidden">
            <Store size={20} />
            <p className="font-bold">Dukaan platform</p>
          </div>
          <h2 className="text-2xl font-bold text-slate-900">Admin sign in</h2>
          <p className="mt-2 text-sm text-slate-500">For the Dukaan product owner only.</p>

          <label className="mt-6 block text-sm font-medium text-slate-700" htmlFor="admin-email">
            Email
          </label>
          <input
            id="admin-email"
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none ring-teal-700 focus:ring-2"
          />

          <label className="mt-4 block text-sm font-medium text-slate-700" htmlFor="admin-password">
            Password
          </label>
          <input
            id="admin-password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none ring-teal-700 focus:ring-2"
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
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>

          <p className="mt-4 text-center text-sm text-slate-500">
            Shop owner?{' '}
            <Link to="/login" className="font-semibold text-teal-700 hover:underline">
              Go to shop login
            </Link>
          </p>
        </form>
      </section>
    </div>
  )
}
