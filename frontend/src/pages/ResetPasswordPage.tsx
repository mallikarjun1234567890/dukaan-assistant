import { Store } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { ApiError, api } from '../services/api'

export function ResetPasswordPage() {
  const [params] = useSearchParams()
  const token = useMemo(() => params.get('token') ?? '', [params])
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (password !== confirm) {
      setError('The two passwords do not match.')
      return
    }
    setError('')
    setSubmitting(true)
    try {
      await api.csrf().catch(() => undefined)
      await api.resetPassword(token, password)
      navigate('/login', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not update the password.')
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
        <h1 className="text-2xl font-bold text-slate-900">Set a new password</h1>
        {!token ? (
          <p className="mt-4 text-sm text-rose-700">This reset link is missing a token. Request a new one.</p>
        ) : (
          <>
            <label className="mt-6 block text-sm font-medium text-slate-700" htmlFor="new-password">
              New password
            </label>
            <input
              id="new-password"
              type="password"
              minLength={8}
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none ring-teal-700 focus:ring-2"
            />
            <label className="mt-4 block text-sm font-medium text-slate-700" htmlFor="confirm-password">
              Confirm password
            </label>
            <input
              id="confirm-password"
              type="password"
              minLength={8}
              required
              value={confirm}
              onChange={(event) => setConfirm(event.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none ring-teal-700 focus:ring-2"
            />
            {error ? (
              <p className="mt-4 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700" role="alert">
                {error}
              </p>
            ) : null}
            <button
              type="submit"
              disabled={submitting}
              className="mt-6 w-full rounded-xl bg-teal-700 px-4 py-2.5 font-semibold text-white disabled:opacity-60"
            >
              {submitting ? 'Saving…' : 'Update password'}
            </button>
          </>
        )}
        <p className="mt-4 text-center text-sm text-slate-500">
          <Link to="/forgot-password" className="font-semibold text-teal-700 hover:underline">
            Request another link
          </Link>
        </p>
      </form>
    </div>
  )
}
