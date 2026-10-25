import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { StatusBadge } from '../components/StatusBadge'
import { api, formatDate, formatINR } from '../services/api'
import type { Invoice } from '../types'

export function InvoiceDetailPage() {
  const { invoiceId } = useParams()
  const [invoice, setInvoice] = useState<Invoice | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!invoiceId) return
    api
      .invoice(Number(invoiceId))
      .then(setInvoice)
      .catch((err: Error) => setError(err.message))
  }, [invoiceId])

  if (error) {
    return <p className="text-sm text-rose-600">{error}</p>
  }
  if (!invoice) {
    return <p className="text-sm text-slate-500">Loading invoice…</p>
  }

  return (
    <div className="space-y-4">
      <div className="no-print flex flex-wrap items-center justify-between gap-3">
        <Link to="/invoices" className="text-sm font-medium text-teal-700 hover:underline">
          Back to invoices
        </Link>
        <button
          type="button"
          onClick={() => window.print()}
          className="rounded-xl bg-teal-700 px-4 py-2 text-sm font-semibold text-white"
        >
          Print / save PDF
        </button>
      </div>

      <article className="print-invoice mx-auto max-w-3xl rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
        <header className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 pb-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-teal-700">Dukaan Assistant</p>
            <h1 className="mt-1 text-2xl font-bold">Tax invoice</h1>
            <p className="text-sm text-slate-500">MVP demo invoice · names and prices are snapshots</p>
          </div>
          <div className="text-right text-sm">
            <p className="font-semibold">{invoice.invoice_number}</p>
            <p className="text-slate-500">{formatDate(invoice.created_at)}</p>
            <div className="mt-2">
              <StatusBadge value={invoice.status} />
            </div>
          </div>
        </header>

        <table className="mt-6 w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-400">
              <th className="py-2">Item</th>
              <th className="py-2">Qty</th>
              <th className="py-2 text-right">Unit price</th>
              <th className="py-2 text-right">Line total</th>
            </tr>
          </thead>
          <tbody>
            {invoice.items.map((item) => (
              <tr key={item.id} className="border-b border-slate-100">
                <td className="py-3">{item.product_name}</td>
                <td className="py-3">{item.quantity}</td>
                <td className="py-3 text-right">{formatINR(item.unit_price)}</td>
                <td className="py-3 text-right">{formatINR(item.line_total)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="mt-6 ml-auto w-full max-w-xs text-sm">
          <div className="flex justify-between py-1">
            <span>Subtotal</span>
            <span>{formatINR(invoice.subtotal)}</span>
          </div>
          <div className="flex justify-between border-t border-slate-200 py-2 text-base font-semibold">
            <span>Grand total</span>
            <span>{formatINR(invoice.total)}</span>
          </div>
        </div>
      </article>
    </div>
  )
}
