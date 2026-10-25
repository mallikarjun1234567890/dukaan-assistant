import { IndianRupee, LogOut, Shield, Store } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Toast } from '../components/Toast'
import { useAuth } from '../context/AuthContext'
import { api, formatDate } from '../services/api'
import type { AdminShop, AdminStats } from '../types'

function planTone(plan: string) {
  if (plan === 'active') return 'bg-emerald-50 text-emerald-800'
  if (plan === 'expired') return 'bg-rose-50 text-rose-800'
  return 'bg-amber-50 text-amber-800'
}

export function AdminDashboardPage() {
  const { user, logout } = useAuth()
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [shops, setShops] = useState<AdminShop[]>([])
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')
  const [busyId, setBusyId] = useState<number | null>(null)

  const load = useCallback(async () => {
    const [nextStats, nextShops] = await Promise.all([api.adminStats(), api.adminShops()])
    setStats(nextStats)
    setShops(nextShops.items)
  }, [])

  useEffect(() => {
    load().catch((err: Error) => setError(err.message))
  }, [load])

  async function run(shopId: number, action: () => Promise<unknown>, ok: string) {
    setBusyId(shopId)
    setError('')
    try {
      await action()
      await load()
      setToast(ok)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Admin action failed')
    } finally {
      setBusyId(null)
    }
  }

  async function onDelete(shop: AdminShop) {
    const confirmed = window.confirm(
      `Delete ${shop.name} and all of its users, products, invoices, and tokens? This cannot be undone.`,
    )
    if (!confirmed) return
    await run(shop.id, () => api.adminDeleteShop(shop.id), `Deleted ${shop.name}`)
  }

  const cards = stats
    ? [
        { label: 'Shops', value: String(stats.total_shops), hint: 'All tenants' },
        { label: 'Trial', value: String(stats.trial_count), hint: '30-day window' },
        { label: 'Active', value: String(stats.active_count), hint: 'Paid or demo' },
        { label: 'Expired', value: String(stats.expired_count), hint: 'Locked shops' },
        {
          label: 'Revenue',
          value: `₹${stats.test_revenue_rupees}`,
          hint: `${stats.successful_pays} test pay(s) · list ₹${stats.list_revenue_rupees}`,
        },
      ]
    : []

  return (
    <div className="min-h-screen bg-[#f3f6f5]">
      <header className="border-b border-slate-200 bg-[#0b3b36] text-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-400 text-[#0b3b36]">
              <Shield size={20} />
            </div>
            <div>
              <p className="text-sm font-bold">Dukaan platform</p>
              <p className="text-xs text-teal-200">{user?.email}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => void logout()}
            className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-teal-100 hover:bg-white/10"
          >
            <LogOut size={16} />
            Logout
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-4 py-6 sm:px-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Shops</h1>
          <p className="mt-1 text-sm text-slate-500">
            Lock, extend trial, mark active, or delete a tenant. Admin cannot edit inventory or invoices.
          </p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {cards.map((card) => (
            <div key={card.label} className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{card.label}</p>
              <p className="mt-2 text-2xl font-bold text-slate-900">{card.value}</p>
              <p className="mt-1 text-xs text-slate-500">{card.hint}</p>
            </div>
          ))}
        </div>

        {error ? (
          <p className="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700" role="alert">
            {error}
          </p>
        ) : null}

        <div className="overflow-x-auto rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium">Shop</th>
                <th className="px-4 py-3 font-medium">Owner</th>
                <th className="px-4 py-3 font-medium">Phone</th>
                <th className="px-4 py-3 font-medium">Plan</th>
                <th className="px-4 py-3 font-medium">Trial end</th>
                <th className="px-4 py-3 font-medium">Paid at</th>
                <th className="px-4 py-3 font-medium">Created</th>
                <th className="px-4 py-3 font-medium">Controls</th>
              </tr>
            </thead>
            <tbody>
              {shops.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-slate-500">
                    <Store className="mx-auto mb-2 text-slate-300" />
                    No shops yet
                  </td>
                </tr>
              ) : (
                shops.map((shop) => (
                  <tr key={shop.id} className="border-b border-slate-100 last:border-0">
                    <td className="px-4 py-3 font-medium text-slate-900">{shop.name}</td>
                    <td className="px-4 py-3 text-slate-600">{shop.owner_email || '—'}</td>
                    <td className="px-4 py-3 text-slate-600">{shop.phone || '—'}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${planTone(shop.plan)}`}>
                        {shop.plan}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {shop.trial_ends_at ? formatDate(shop.trial_ends_at) : '—'}
                    </td>
                    <td className="px-4 py-3 text-slate-600">{shop.paid_at ? formatDate(shop.paid_at) : '—'}</td>
                    <td className="px-4 py-3 text-slate-600">{formatDate(shop.created_at)}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        <button
                          type="button"
                          disabled={busyId === shop.id}
                          onClick={() => void run(shop.id, () => api.adminLockShop(shop.id), `Locked ${shop.name}`)}
                          className="rounded-lg bg-rose-50 px-2 py-1 text-xs font-medium text-rose-700 disabled:opacity-50"
                        >
                          Lock
                        </button>
                        <button
                          type="button"
                          disabled={busyId === shop.id}
                          onClick={() =>
                            void run(shop.id, () => api.adminExtendTrial(shop.id), `Extended trial for ${shop.name}`)
                          }
                          className="rounded-lg bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800 disabled:opacity-50"
                        >
                          Extend trial
                        </button>
                        <button
                          type="button"
                          disabled={busyId === shop.id}
                          onClick={() =>
                            void run(shop.id, () => api.adminMarkActive(shop.id), `Marked ${shop.name} active`)
                          }
                          className="rounded-lg bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-800 disabled:opacity-50"
                        >
                          Mark active
                        </button>
                        <button
                          type="button"
                          disabled={busyId === shop.id}
                          onClick={() => void onDelete(shop)}
                          className="rounded-lg bg-slate-900 px-2 py-1 text-xs font-medium text-white disabled:opacity-50"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <p className="flex items-center gap-2 text-xs text-slate-400">
          <IndianRupee size={12} />
          Test-mode revenue is ₹1 × successful pays. List price is ₹499/month.
        </p>
      </main>
      {toast ? <Toast message={toast} tone="success" /> : null}
    </div>
  )
}
