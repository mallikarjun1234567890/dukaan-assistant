import { useEffect, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { EmptyState } from '../components/EmptyState'
import { Modal } from '../components/Modal'
import { StatusBadge } from '../components/StatusBadge'
import { Toast } from '../components/Toast'
import { api, formatINR } from '../services/api'
import type { Product } from '../types'

interface ProductForm {
  name: string
  sku: string
  category: string
  selling_price: string
  purchase_cost: string
  stock_quantity: string
  minimum_stock: string
  supplier_name: string
}

const emptyForm: ProductForm = {
  name: '',
  sku: '',
  category: '',
  selling_price: '',
  purchase_cost: '',
  stock_quantity: '',
  minimum_stock: '',
  supplier_name: '',
}

function digitsOnly(value: string): boolean {
  return value === '' || /^\d+$/.test(value)
}

function moneyOnly(value: string): boolean {
  return value === '' || /^\d*\.?\d{0,2}$/.test(value)
}

export function InventoryPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [stockStatus, setStockStatus] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Product | null>(null)
  const [form, setForm] = useState<ProductForm>(emptyForm)
  const [saving, setSaving] = useState(false)
  const [detail, setDetail] = useState<Product | null>(null)
  const [toDelete, setToDelete] = useState<Product | null>(null)
  const [photo, setPhoto] = useState<File | null>(null)
  const [photoBusy, setPhotoBusy] = useState(false)

  async function load() {
    setError('')
    try {
      const data = await api.products({
        search: search || undefined,
        category: category || undefined,
        stock_status: stockStatus || undefined,
      })
      setProducts(data.items)
      setCategories(data.categories)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load products')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const handle = window.setTimeout(() => {
      void load()
    }, 200)
    return () => window.clearTimeout(handle)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, category, stockStatus])

  function openCreate() {
    setEditing(null)
    setForm(emptyForm)
    setPhoto(null)
    setFormOpen(true)
  }

  function openEdit(product: Product) {
    setEditing(product)
    setForm({
      name: product.name,
      sku: product.sku,
      category: product.category,
      selling_price: String(product.selling_price),
      purchase_cost: String(product.purchase_cost),
      stock_quantity: String(product.stock_quantity),
      minimum_stock: String(product.minimum_stock),
      supplier_name: product.supplier_name,
    })
    setPhoto(null)
    setFormOpen(true)
  }

  async function onSave(event: FormEvent) {
    event.preventDefault()
    const stock = Number(form.stock_quantity)
    const minimum = Number(form.minimum_stock)
    if (!Number.isInteger(stock) || stock < 0 || !Number.isInteger(minimum) || minimum < 0) {
      setError('Stock and minimum stock must be whole numbers. You can leave them empty only before typing.')
      return
    }
    const payload = {
      ...form,
      stock_quantity: stock,
      minimum_stock: minimum,
    }
    setSaving(true)
    setError('')
    try {
      const saved = editing
        ? await api.updateProduct(editing.id, payload)
        : await api.createProduct(payload)
      if (photo) {
        await api.upload(photo, 'product', saved.id)
      }
      setToast(editing ? 'Product updated' : 'Product added')
      setFormOpen(false)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save product')
    } finally {
      setSaving(false)
    }
  }

  async function confirmDelete() {
    if (!toDelete) return
    try {
      await api.deleteProduct(toDelete.id)
      setToast('Product deleted')
      setToDelete(null)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete product')
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Inventory</h1>
          <p className="mt-1 text-sm text-slate-500">Search, filter, and keep stock thresholds up to date.</p>
        </div>
        <button
          type="button"
          onClick={openCreate}
          className="rounded-xl bg-teal-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-teal-800"
        >
          Add product
        </button>
      </div>

      <div className="grid gap-3 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200 md:grid-cols-3">
        <label className="text-sm">
          <span className="mb-1 block font-medium text-slate-600">Search name or SKU</span>
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            className="w-full rounded-xl border border-slate-200 px-3 py-2"
            placeholder="Fortune oil…"
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium text-slate-600">Category</span>
          <select
            value={category}
            onChange={(event) => setCategory(event.target.value)}
            className="w-full rounded-xl border border-slate-200 px-3 py-2"
          >
            <option value="">All categories</option>
            {categories.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium text-slate-600">Stock status</span>
          <select
            value={stockStatus}
            onChange={(event) => setStockStatus(event.target.value)}
            className="w-full rounded-xl border border-slate-200 px-3 py-2"
          >
            <option value="">All</option>
            <option value="healthy">Healthy</option>
            <option value="low">Low</option>
            <option value="out">Out of stock</option>
          </select>
        </label>
      </div>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      {loading ? (
        <p className="text-sm text-slate-500">Loading products…</p>
      ) : products.length === 0 ? (
        <EmptyState
          title="No products match"
          description="Add a product or clear filters to see your catalog."
          action={
            <button type="button" onClick={openCreate} className="rounded-xl bg-teal-700 px-4 py-2 text-white">
              Add product
            </button>
          }
        />
      ) : (
        <div className="overflow-x-auto rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-4 py-3">Product</th>
                <th className="px-4 py-3">SKU</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Price</th>
                <th className="px-4 py-3">Stock</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <tr key={product.id} className="border-t border-slate-100">
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      onClick={() => setDetail(product)}
                      className="flex items-center gap-2 font-medium text-teal-800 hover:underline"
                    >
                      {product.image_url ? (
                        <img src={product.image_url} alt="" className="h-8 w-8 rounded-lg object-cover" />
                      ) : null}
                      {product.name}
                    </button>
                    {product.is_low_stock ? (
                      <p className="text-xs text-amber-600">Below minimum ({product.minimum_stock})</p>
                    ) : null}
                  </td>
                  <td className="px-4 py-3 text-slate-500">{product.sku}</td>
                  <td className="px-4 py-3">{product.category}</td>
                  <td className="px-4 py-3">{formatINR(product.selling_price)}</td>
                  <td className="px-4 py-3">{product.stock_quantity}</td>
                  <td className="px-4 py-3">
                    <StatusBadge value={product.stock_status} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button type="button" onClick={() => openEdit(product)} className="text-teal-700 hover:underline">
                        Edit
                      </button>
                      <button type="button" onClick={() => setToDelete(product)} className="text-rose-600 hover:underline">
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {formOpen ? (
        <Modal title={editing ? 'Edit product' : 'Add product'} onClose={() => setFormOpen(false)} wide>
          <form onSubmit={onSave} className="grid gap-3 sm:grid-cols-2">
            <Field label="Product name" htmlFor="name">
              <input
                id="name"
                required
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                className="w-full rounded-xl border border-slate-200 px-3 py-2"
              />
            </Field>
            <Field label="SKU" htmlFor="sku">
              <input
                id="sku"
                required
                value={form.sku}
                onChange={(event) => setForm({ ...form, sku: event.target.value })}
                className="w-full rounded-xl border border-slate-200 px-3 py-2"
              />
            </Field>
            <Field label="Category" htmlFor="category">
              <input
                id="category"
                required
                value={form.category}
                onChange={(event) => setForm({ ...form, category: event.target.value })}
                className="w-full rounded-xl border border-slate-200 px-3 py-2"
              />
            </Field>
            <Field label="Supplier" htmlFor="supplier">
              <input
                id="supplier"
                value={form.supplier_name}
                onChange={(event) => setForm({ ...form, supplier_name: event.target.value })}
                className="w-full rounded-xl border border-slate-200 px-3 py-2"
              />
            </Field>
            <Field label="Selling price (₹)" htmlFor="selling">
              <input
                id="selling"
                required
                inputMode="decimal"
                value={form.selling_price}
                onChange={(event) => {
                  if (moneyOnly(event.target.value)) setForm({ ...form, selling_price: event.target.value })
                }}
                className="w-full rounded-xl border border-slate-200 px-3 py-2"
              />
            </Field>
            <Field label="Purchase cost (₹)" htmlFor="cost">
              <input
                id="cost"
                required
                inputMode="decimal"
                value={form.purchase_cost}
                onChange={(event) => {
                  if (moneyOnly(event.target.value)) setForm({ ...form, purchase_cost: event.target.value })
                }}
                className="w-full rounded-xl border border-slate-200 px-3 py-2"
              />
            </Field>
            <Field label="Stock quantity" htmlFor="stock">
              <input
                id="stock"
                required
                inputMode="numeric"
                value={form.stock_quantity}
                onChange={(event) => {
                  if (digitsOnly(event.target.value)) setForm({ ...form, stock_quantity: event.target.value })
                }}
                className="w-full rounded-xl border border-slate-200 px-3 py-2"
              />
            </Field>
            <Field label="Minimum stock" htmlFor="minimum">
              <input
                id="minimum"
                required
                inputMode="numeric"
                value={form.minimum_stock}
                onChange={(event) => {
                  if (digitsOnly(event.target.value)) setForm({ ...form, minimum_stock: event.target.value })
                }}
                className="w-full rounded-xl border border-slate-200 px-3 py-2"
              />
            </Field>
            <label className="sm:col-span-2 text-sm">
              <span className="mb-1 block font-medium text-slate-600">Product photo (Cloudinary)</span>
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={(event) => setPhoto(event.target.files?.[0] ?? null)}
                className="w-full text-xs"
              />
            </label>
            <div className="sm:col-span-2 mt-2 flex justify-end gap-2">
              <button type="button" onClick={() => setFormOpen(false)} className="rounded-xl px-4 py-2 text-slate-600">
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="rounded-xl bg-teal-700 px-4 py-2 font-semibold text-white disabled:opacity-60"
              >
                {saving ? 'Saving…' : 'Save product'}
              </button>
            </div>
          </form>
        </Modal>
      ) : null}

      {detail ? (
        <Modal title={detail.name} onClose={() => setDetail(null)}>
          {detail.image_url ? (
            <img src={detail.image_url} alt="" className="mb-3 h-28 w-28 rounded-xl object-cover ring-1 ring-slate-200" />
          ) : null}
          <label className="mb-4 block text-sm">
            <span className="mb-1 block font-medium text-slate-600">Replace photo</span>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              disabled={photoBusy}
              onChange={async (event) => {
                const file = event.target.files?.[0]
                event.target.value = ''
                if (!file) return
                setPhotoBusy(true)
                setError('')
                try {
                  const result = await api.upload(file, 'product', detail.id)
                  const next = { ...detail, image_url: result.url }
                  setDetail(next)
                  setProducts((current) => current.map((item) => (item.id === next.id ? next : item)))
                  setToast('Product photo updated')
                } catch (err) {
                  setError(err instanceof Error ? err.message : 'Could not upload image')
                } finally {
                  setPhotoBusy(false)
                }
              }}
              className="w-full text-xs"
            />
          </label>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-slate-500">SKU</dt>
              <dd className="font-medium">{detail.sku}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Category</dt>
              <dd className="font-medium">{detail.category}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Selling price</dt>
              <dd className="font-medium">{formatINR(detail.selling_price)}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Purchase cost</dt>
              <dd className="font-medium">{formatINR(detail.purchase_cost)}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Stock</dt>
              <dd className="font-medium">{detail.stock_quantity}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Minimum</dt>
              <dd className="font-medium">{detail.minimum_stock}</dd>
            </div>
            <div className="col-span-2">
              <dt className="text-slate-500">Supplier</dt>
              <dd className="font-medium">{detail.supplier_name || '—'}</dd>
            </div>
          </dl>
        </Modal>
      ) : null}

      {toDelete ? (
        <Modal title="Delete product?" onClose={() => setToDelete(null)}>
          <p className="text-sm text-slate-600">
            Delete <strong>{toDelete.name}</strong>? This cannot be undone.
          </p>
          <div className="mt-5 flex justify-end gap-2">
            <button type="button" onClick={() => setToDelete(null)} className="rounded-xl px-4 py-2">
              Cancel
            </button>
            <button type="button" onClick={() => void confirmDelete()} className="rounded-xl bg-rose-600 px-4 py-2 text-white">
              Delete
            </button>
          </div>
        </Modal>
      ) : null}

      {toast ? <Toast message={toast} tone="success" /> : null}
    </div>
  )
}

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string
  htmlFor: string
  children: ReactNode
}) {
  return (
    <label className="text-sm" htmlFor={htmlFor}>
      <span className="mb-1 block font-medium text-slate-600">{label}</span>
      {children}
    </label>
  )
}
