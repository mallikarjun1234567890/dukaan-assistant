import { useEffect, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import { Toast } from '../components/Toast'
import { useAuth } from '../context/AuthContext'
import { api, formatDate } from '../services/api'
import { startSubscriptionCheckout } from '../services/razorpay'
import type { BillingConfig, ShopSettings } from '../types'

const weekdays = ['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

function planLabel(plan?: string) {
  if (plan === 'active') return 'Active'
  if (plan === 'expired') return 'Expired'
  return 'Trial'
}

export function SettingsPage() {
  const { user, refresh } = useAuth()
  const [form, setForm] = useState<ShopSettings | null>(null)
  const [billing, setBilling] = useState<BillingConfig | null>(null)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState('')
  const [paying, setPaying] = useState(false)

  useEffect(() => {
    api
      .shop()
      .then(setForm)
      .catch((err: Error) => setError(err.message))
    api.billingConfig().then(setBilling).catch(() => undefined)
    void refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function onSave(event: FormEvent) {
    event.preventDefault()
    if (!form) return
    setSaving(true)
    setError('')
    try {
      const saved = await api.updateShop({
        name: form.name,
        phone: form.phone,
        timezone: form.timezone,
        opens_at: form.opens_at,
        closes_at: form.closes_at,
        weekly_off: form.weekly_off,
      })
      setForm(saved)
      setToast('Shop hours saved')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save settings')
    } finally {
      setSaving(false)
    }
  }

  async function onPhoto(kind: 'shop_logo' | 'avatar', event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    setUploading(kind)
    setError('')
    try {
      const result = await api.upload(file, kind)
      if (kind === 'shop_logo') {
        setForm((current) => (current ? { ...current, logo_url: result.url } : current))
        setToast('Shop logo updated')
      } else {
        await refresh()
        setToast('Profile photo updated')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not upload image')
    } finally {
      setUploading('')
    }
  }

  async function subscribe() {
    setPaying(true)
    setError('')
    try {
      await startSubscriptionCheckout({
        onSuccess: async (plan) => {
          setBilling((current) => (current ? { ...current, plan } : current))
          setForm((current) => (current ? { ...current, plan } : current))
          setToast('Subscription is now active')
          await refresh()
          const latest = await api.billingConfig()
          setBilling(latest)
          const shop = await api.shop()
          setForm(shop)
        },
        onError: (message) => setError(message),
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start Razorpay')
    } finally {
      setPaying(false)
    }
  }

  if (!form) {
    return <p className="text-sm text-slate-500">{error || 'Loading shop settings…'}</p>
  }

  const plan = form.plan || billing?.plan || 'trial'

  return (
    <div className="mx-auto max-w-xl space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Shop settings</h1>
        <p className="mt-1 text-sm text-slate-500">Hours stay on this page. Photos use Cloudinary.</p>
      </div>

      <div className={`rounded-2xl px-4 py-3 text-sm ${form.is_open ? 'bg-emerald-50 text-emerald-800' : 'bg-amber-50 text-amber-800'}`}>
        {form.weekday} {form.local_time} · shop is {form.is_open ? 'open' : 'closed'}
      </div>

      <section className="space-y-3 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h2 className="font-semibold text-slate-900">Plan</h2>
        <p className="text-sm text-slate-600">
          Current plan: <strong>{planLabel(plan)}</strong>
        </p>
        {form.trial_ends_at ? (
          <p className="text-sm text-slate-500">Trial ends {formatDate(form.trial_ends_at)}</p>
        ) : null}
        {form.plan_expires_at ? (
          <p className="text-sm text-slate-500">Paid access until {formatDate(form.plan_expires_at)}</p>
        ) : null}
        {form.paid_at ? <p className="text-sm text-slate-500">Last paid {formatDate(form.paid_at)}</p> : null}
        {plan === 'active' ? (
          <p className="text-sm text-emerald-700">Your shop is on the ₹499/month plan.</p>
        ) : billing?.enabled ? (
          <>
            <p className="text-sm text-slate-500">
              Subscribe <strong>₹499/month</strong>. Test charge ₹1.
            </p>
            <button
              type="button"
              onClick={() => void subscribe()}
              disabled={paying}
              className="rounded-xl bg-teal-700 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60"
            >
              {paying ? 'Opening checkout…' : 'Subscribe ₹499/month'}
            </button>
          </>
        ) : (
          <p className="text-sm text-slate-500">
            Add Razorpay test keys in the backend environment to enable checkout. The shop stays usable during
            the trial.
          </p>
        )}
      </section>

      <section className="space-y-4 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h2 className="font-semibold text-slate-900">Photos</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="text-sm">
            <span className="mb-2 block font-medium text-slate-600">Shop logo</span>
            {form.logo_url ? (
              <img
                src={form.logo_url}
                alt="Shop logo"
                className="mb-2 h-24 w-24 rounded-xl bg-slate-100 object-cover ring-1 ring-slate-200"
              />
            ) : (
              <div className="mb-2 flex h-24 w-24 items-center justify-center rounded-xl bg-slate-100 text-xs text-slate-400 ring-1 ring-slate-200">
                No logo
              </div>
            )}
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(event) => void onPhoto('shop_logo', event)}
              disabled={Boolean(uploading)}
              className="w-full text-xs"
            />
            {uploading === 'shop_logo' ? <p className="mt-1 text-xs text-slate-500">Uploading…</p> : null}
          </label>
          <label className="text-sm">
            <span className="mb-2 block font-medium text-slate-600">Profile photo</span>
            {user?.avatar_url ? (
              <img
                src={user.avatar_url}
                alt=""
                className="mb-2 h-24 w-24 rounded-xl bg-slate-100 object-cover ring-1 ring-slate-200"
              />
            ) : (
              <div className="mb-2 flex h-24 w-24 items-center justify-center rounded-xl bg-slate-100 text-xs text-slate-400 ring-1 ring-slate-200">
                No photo
              </div>
            )}
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(event) => void onPhoto('avatar', event)}
              disabled={Boolean(uploading)}
              className="w-full text-xs"
            />
            {uploading === 'avatar' ? <p className="mt-1 text-xs text-slate-500">Uploading…</p> : null}
          </label>
        </div>
      </section>

      <form onSubmit={onSave} className="space-y-4 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-600">Shop name</span>
          <input
            required
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            className="w-full rounded-xl border border-slate-200 px-3 py-2"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-600">Phone</span>
          <input
            value={form.phone}
            onChange={(event) => setForm({ ...form, phone: event.target.value })}
            className="w-full rounded-xl border border-slate-200 px-3 py-2"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-600">Timezone</span>
          <input
            value={form.timezone}
            onChange={(event) => setForm({ ...form, timezone: event.target.value })}
            className="w-full rounded-xl border border-slate-200 px-3 py-2"
          />
        </label>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-sm">
            <span className="mb-1 block font-medium text-slate-600">Opens at</span>
            <input
              type="time"
              value={form.opens_at}
              onChange={(event) => setForm({ ...form, opens_at: event.target.value })}
              className="w-full rounded-xl border border-slate-200 px-3 py-2"
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium text-slate-600">Closes at</span>
            <input
              type="time"
              value={form.closes_at}
              onChange={(event) => setForm({ ...form, closes_at: event.target.value })}
              className="w-full rounded-xl border border-slate-200 px-3 py-2"
            />
          </label>
        </div>
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-600">Weekly off</span>
          <select
            value={form.weekly_off}
            onChange={(event) => setForm({ ...form, weekly_off: event.target.value })}
            className="w-full rounded-xl border border-slate-200 px-3 py-2"
          >
            {weekdays.map((day) => (
              <option key={day || 'none'} value={day}>
                {day || 'None'}
              </option>
            ))}
          </select>
        </label>
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        <button
          type="submit"
          disabled={saving}
          className="w-full rounded-xl bg-teal-700 px-4 py-2.5 font-semibold text-white disabled:opacity-60"
        >
          {saving ? 'Saving…' : 'Save hours'}
        </button>
      </form>
      {toast ? <Toast message={toast} tone="success" /> : null}
    </div>
  )
}
