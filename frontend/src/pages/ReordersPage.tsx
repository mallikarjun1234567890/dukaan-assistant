import { useEffect, useState } from 'react'
import { EmptyState } from '../components/EmptyState'
import { StatusBadge } from '../components/StatusBadge'
import { Toast } from '../components/Toast'
import { api, formatINR } from '../services/api'
import type { ReorderItem } from '../types'

export function ReordersPage() {
  const [items, setItems] = useState<ReorderItem[]>([])
  const [rule, setRule] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState('')
  const [busyId, setBusyId] = useState<number | null>(null)

  async function load() {
    try {
      const data = await api.reorders()
      setItems(data.items)
      setRule(data.rule)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load recommendations')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function act(id: number, action: 'approve' | 'reject') {
    setBusyId(id)
    setError('')
    try {
      if (action === 'approve') {
        await api.approveReorder(id)
        setToast('Internal reorder request approved')
      } else {
        await api.rejectReorder(id)
        setToast('Recommendation rejected')
      }
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update recommendation')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Reorder recommendations</h1>
        <p className="mt-1 text-sm text-slate-500">
          {rule ||
            'Suggested quantity = max(0, 2 × minimum stock − current stock). Approval is internal only.'}
        </p>
      </div>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      {loading ? (
        <p className="text-sm text-slate-500">Calculating recommendations…</p>
      ) : items.length === 0 ? (
        <EmptyState
          title="No recommendations"
          description="When stock falls to the minimum threshold, a suggestion will appear here."
        />
      ) : (
        <div className="overflow-x-auto rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-400">
              <tr>
                <th className="px-4 py-3">Product</th>
                <th className="px-4 py-3">Stock</th>
                <th className="px-4 py-3">Minimum</th>
                <th className="px-4 py-3">Suggested qty</th>
                <th className="px-4 py-3">Supplier</th>
                <th className="px-4 py-3">Est. cost</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-t border-slate-100">
                  <td className="px-4 py-3">
                    <p className="font-medium">{item.product_name}</p>
                    <p className="text-xs text-slate-400">{item.sku}</p>
                  </td>
                  <td className="px-4 py-3">{item.current_stock}</td>
                  <td className="px-4 py-3">{item.minimum_stock}</td>
                  <td className="px-4 py-3 font-semibold">{item.suggested_quantity}</td>
                  <td className="px-4 py-3">{item.supplier_name || '—'}</td>
                  <td className="px-4 py-3">{formatINR(item.estimated_cost)}</td>
                  <td className="px-4 py-3">
                    <StatusBadge value={item.status} />
                  </td>
                  <td className="px-4 py-3">
                    {item.status === 'pending' ? (
                      <div className="flex gap-2">
                        <button
                          type="button"
                          disabled={busyId === item.id}
                          onClick={() => void act(item.id, 'approve')}
                          className="rounded-lg bg-teal-700 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-60"
                        >
                          Approve
                        </button>
                        <button
                          type="button"
                          disabled={busyId === item.id}
                          onClick={() => void act(item.id, 'reject')}
                          className="rounded-lg px-3 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-50"
                        >
                          Reject
                        </button>
                      </div>
                    ) : (
                      <span className="text-xs text-slate-400">No further action</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {toast ? <Toast message={toast} tone="success" /> : null}
    </div>
  )
}
