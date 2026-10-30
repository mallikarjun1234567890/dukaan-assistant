import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../components/EmptyState'
import { StatusBadge } from '../components/StatusBadge'
import { Toast } from '../components/Toast'
import { api, formatDate, formatINR } from '../services/api'
import type { Invoice, Product } from '../types'

interface LineDraft {
  productId: number
  quantity: string
}

function parseQuantityInput(raw: string): string {
  const digits = raw.replace(/\D/g, '')
  if (digits === '') return ''
  return String(Number.parseInt(digits, 10))
}

function quantityValue(raw: string): number {
  const parsed = Number.parseInt(raw, 10)
  return Number.isFinite(parsed) ? parsed : 0
}

export function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [lines, setLines] = useState<LineDraft[]>([{ productId: 0, quantity: '1' }])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState('')
  const [idempotencyKey, setIdempotencyKey] = useState(() => crypto.randomUUID())

  async function load() {
    try {
      const [invoiceData, productData] = await Promise.all([api.invoices(), api.products()])
      setInvoices(invoiceData.items)
      setProducts(productData.items)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load invoices')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const preview = useMemo(() => {
    return lines
      .filter((line) => line.productId && quantityValue(line.quantity) > 0)
      .map((line) => {
        const product = products.find((item) => item.id === line.productId)
        const unit = product ? Number(product.selling_price) : 0
        const quantity = quantityValue(line.quantity)
        return {
          product,
          quantity,
          unit,
          total: unit * quantity,
        }
      })
  }, [lines, products])

  const previewTotal = preview.reduce((sum, line) => sum + line.total, 0)

  async function createInvoice() {
    setError('')
    const items = lines
      .filter((line) => line.productId && quantityValue(line.quantity) > 0)
      .map((line) => ({ product_id: line.productId, quantity: quantityValue(line.quantity) }))
    if (items.length === 0) {
      setError('Add at least one product with a quantity greater than zero.')
      return
    }
    setSaving(true)
    try {
      const invoice = await api.createInvoice(items, idempotencyKey)
      setToast(`Invoice ${invoice.invoice_number} created`)
      setLines([{ productId: 0, quantity: '1' }])
      setIdempotencyKey(crypto.randomUUID())
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create invoice')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Invoices and Sales</h1>
        <p className="mt-1 text-sm text-slate-500">
          Totals are calculated by the server. Stock is deducted once, inside a single transaction.
        </p>
      </div>

      <section className="grid gap-6 xl:grid-cols-2">
        <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
          <h2 className="font-semibold text-slate-900">New invoice</h2>
          <div className="mt-4 space-y-3">
            {lines.map((line, index) => (
              <div key={`${line.productId}-${index}`} className="grid gap-2 sm:grid-cols-[1fr_100px_auto]">
                <label className="text-sm">
                  <span className="sr-only">Product</span>
                  <select
                    value={line.productId}
                    onChange={(event) => {
                      const next = [...lines]
                      next[index] = { ...line, productId: Number(event.target.value) }
                      setLines(next)
                    }}
                    className="w-full rounded-xl border border-slate-200 px-3 py-2"
                  >
                    <option value={0}>Select product</option>
                    {products.map((product) => (
                      <option key={product.id} value={product.id}>
                        {product.name} · stock {product.stock_quantity}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-sm">
                  <span className="sr-only">Quantity</span>
                  <input
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    autoComplete="off"
                    value={line.quantity}
                    onChange={(event) => {
                      const next = [...lines]
                      next[index] = { ...line, quantity: parseQuantityInput(event.target.value) }
                      setLines(next)
                    }}
                    className="w-full rounded-xl border border-slate-200 px-3 py-2"
                  />
                </label>
                <button
                  type="button"
                  onClick={() => setLines(lines.filter((_, itemIndex) => itemIndex !== index))}
                  className="text-sm text-rose-600"
                  disabled={lines.length === 1}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={() => setLines([...lines, { productId: 0, quantity: '1' }])}
            className="mt-3 text-sm font-medium text-teal-700"
          >
            Add line
          </button>
          {error ? <p className="mt-3 text-sm text-rose-600">{error}</p> : null}
          <button
            type="button"
            onClick={() => void createInvoice()}
            disabled={saving}
            className="mt-4 w-full rounded-xl bg-teal-700 px-4 py-2.5 font-semibold text-white disabled:opacity-60"
          >
            {saving ? 'Saving invoice…' : 'Save invoice'}
          </button>
        </div>

        <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
          <h2 className="font-semibold text-slate-900">Preview</h2>
          <p className="mt-1 text-xs text-slate-400">
            Preview uses current catalog prices. The backend recalculates and stores the official total.
          </p>
          {preview.length === 0 ? (
            <p className="mt-6 text-sm text-slate-500">Select products to preview the bill.</p>
          ) : (
            <table className="mt-4 w-full text-sm">
              <thead className="text-left text-xs uppercase text-slate-400">
                <tr>
                  <th className="pb-2">Item</th>
                  <th className="pb-2">Qty</th>
                  <th className="pb-2 text-right">Amount</th>
                </tr>
              </thead>
              <tbody>
                {preview.map((line) => (
                  <tr key={line.product?.id} className="border-t border-slate-100">
                    <td className="py-2">{line.product?.name}</td>
                    <td className="py-2">{line.quantity}</td>
                    <td className="py-2 text-right">{formatINR(line.total)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t border-slate-200">
                  <td className="pt-3 font-semibold" colSpan={2}>
                    Grand total
                  </td>
                  <td className="pt-3 text-right font-semibold">{formatINR(previewTotal)}</td>
                </tr>
              </tfoot>
            </table>
          )}
        </div>
      </section>

      <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h2 className="font-semibold text-slate-900">Invoice history</h2>
        {loading ? (
          <p className="mt-4 text-sm text-slate-500">Loading invoices…</p>
        ) : invoices.length === 0 ? (
          <div className="mt-4">
            <EmptyState title="No invoices yet" description="Save an invoice to start tracking sales." />
          </div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase text-slate-400">
                <tr>
                  <th className="pb-2 pr-4">Number</th>
                  <th className="pb-2 pr-4">Total</th>
                  <th className="pb-2 pr-4">Status</th>
                  <th className="pb-2">Created</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((invoice) => (
                  <tr key={invoice.id} className="border-t border-slate-100">
                    <td className="py-3 pr-4 font-medium">
                      <Link to={`/invoices/${invoice.id}`} className="text-teal-800 hover:underline">
                        {invoice.invoice_number}
                      </Link>
                    </td>
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
      {toast ? <Toast message={toast} tone="success" /> : null}
    </div>
  )
}
