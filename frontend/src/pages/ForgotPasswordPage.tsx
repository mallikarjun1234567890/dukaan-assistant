import { Store } from 'lucide-react'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ApiError, api } from '../services/api'

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [done, setDone] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setDone('')
    setSubmitting(true)
    try {
      await api.csrf().catch(() => undefined)
      const result = await api.forgotPassword(email)
      setDone(result.detail)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not send the reset email.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-12">
      <form onSubmit={onSubmit} className="w-full max-w-md rounded-3xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
        <div className="mb-6 flex items-center gap-2 text-teal-800">
          <Store size={20} />
          <p className="font-bold">Dukaan Assistant</p>
        </div>
        <h1 className="text-2xl font-bold text-slate-900">Forgot password</h1>
        <p className="mt-2 text-sm text-slate-500">
          Enter the email for your shop. If it is registered, we will send a reset link.
        </p>
        <label className="mt-6 block text-sm font-medium text-slate-700" htmlFor="reset-email">
          Email
        </label>
        <input
          id="reset-email"
          type="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none ring-teal-700 focus:ring-2"
        />
        {error ? (
          <p className="mt-4 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700" role="alert">
            {error}
          </p>
        ) : null}
        {done ? (
          <p className="mt-4 rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-800" role="status">
            {done}
          </p>
        ) : null}
        <button
          type="submit"
          disabled={submitting}
          className="mt-6 w-full rounded-xl bg-teal-700 px-4 py-2.5 font-semibold text-white disabled:opacity-60"
        >
          {submitting ? 'Sending…' : 'Send reset link'}
        </button>
        <p className="mt-4 text-center text-sm text-slate-500">
          <Link to="/login" className="font-semibold text-teal-700 hover:underline">
            Back to sign in
          </Link>
        </p>
      </form>
    </div>
  )
}
