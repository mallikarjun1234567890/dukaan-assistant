import { AlertTriangle, IndianRupee, Package, Receipt } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { EmptyState } from '../components/EmptyState'
import { StatusBadge } from '../components/StatusBadge'
import { api, formatDate, formatINR } from '../services/api'
import type { DashboardData } from '../types'

export function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .dashboard()
      .then(setData)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <p className="text-sm text-slate-500">Loading dashboard…</p>
  }
  if (error || !data) {
    return <p className="text-sm text-rose-600">{error || 'Dashboard data unavailable.'}</p>
  }

  const cards = [
    { label: 'Products', value: String(data.product_count), icon: Package, hint: 'In your catalog' },
    {
      label: 'Inventory value',
      value: formatINR(data.inventory_value),
      icon: IndianRupee,
      hint: 'Stock × purchase cost',
    },
    { label: 'Low stock', value: String(data.low_stock_count), icon: AlertTriangle, hint: 'At or below minimum' },
    {
      label: "Today's confirmed sales",
      value: formatINR(data.today_sales),
      icon: Receipt,
      hint: `${data.today_invoice_count} invoice(s) today`,
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium text-teal-700">{data.shop_name}</p>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-500">
          {data.weekday} {data.local_time} · shop is {data.is_open ? 'open' : 'closed'} ({data.opens_at}–
          {data.closes_at}
          {data.weekly_off ? `, weekly off ${data.weekly_off}` : ''}). Sales use confirmed invoices only.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => {
          const Icon = card.icon
          return (
            <article key={card.label} className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
              <div className="flex items-center justify-between">
                <p className="text-sm text-slate-500">{card.label}</p>
                <span className="rounded-lg bg-teal-50 p-2 text-teal-700">
                  <Icon size={18} />
                </span>
              </div>
              <p className="mt-3 text-2xl font-bold text-slate-900">{card.value}</p>
              <p className="mt-1 text-xs text-slate-400">{card.hint}</p>
            </article>
          )
        })}
      </div>

      <div className="grid gap-6 xl:grid-cols-5">
        <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 xl:col-span-3">
          <h2 className="font-semibold text-slate-900">Lowest stock levels</h2>
          {data.stock_levels.length === 0 ? (
            <EmptyState title="No products yet" description="Add inventory to see stock levels." />
          ) : (
            <div className="mt-4 h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.stock_levels} margin={{ left: 0, right: 8, top: 8, bottom: 24 }}>
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-20} textAnchor="end" height={60} />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="stock_quantity" fill="#0f766e" radius={[6, 6, 0, 0]} name="Current stock" />
                  <Bar dataKey="minimum_stock" fill="#f59e0b" radius={[6, 6, 0, 0]} name="Minimum" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </section>

        <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 xl:col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-slate-900">Stock summary</h2>
            <Link to="/reorders" className="text-sm font-medium text-teal-700 hover:underline">
              View reorders
            </Link>
          </div>
          <ul className="mt-4 space-y-3 text-sm">
            <li className="flex justify-between rounded-xl bg-emerald-50 px-3 py-2 text-emerald-800">
              <span>Healthy</span>
              <strong>{data.stock_summary.healthy}</strong>
            </li>
            <li className="flex justify-between rounded-xl bg-amber-50 px-3 py-2 text-amber-800">
              <span>Low</span>
              <strong>{data.stock_summary.low}</strong>
            </li>
            <li className="flex justify-between rounded-xl bg-rose-50 px-3 py-2 text-rose-800">
              <span>Out of stock</span>
              <strong>{data.stock_summary.out}</strong>
            </li>
          </ul>
        </section>
      </div>

      <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-slate-900">Recent invoices</h2>
          <Link to="/invoices" className="text-sm font-medium text-teal-700 hover:underline">
            Create invoice
          </Link>
        </div>
        {data.recent_invoices.length === 0 ? (
          <div className="mt-4">
            <EmptyState title="No invoices yet" description="Generate a bill from Invoices and Sales." />
          </div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="pb-2 pr-4">Invoice</th>
                  <th className="pb-2 pr-4">Items</th>
                  <th className="pb-2 pr-4">Total</th>
                  <th className="pb-2 pr-4">Status</th>
                  <th className="pb-2">Created</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_invoices.map((invoice) => (
                  <tr key={invoice.id} className="border-t border-slate-100">
                    <td className="py-3 pr-4 font-medium">
                      <Link to={`/invoices/${invoice.id}`} className="text-teal-800 hover:underline">
                        {invoice.invoice_number}
                      </Link>
                    </td>
                    <td className="py-3 pr-4">{invoice.item_count}</td>
                    <td className="py-3 pr-4">{formatINR(invoice.total)}</td>
                    <td className="py-3 pr-4">
                      <StatusBadge value={invoice.status} />
                    </td>
                    <td className="py-3 text-slate-500">{formatDate(invoice.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
