const styles: Record<string, string> = {
  healthy: 'bg-emerald-50 text-emerald-700 ring-emerald-100',
  low: 'bg-amber-50 text-amber-700 ring-amber-100',
  out: 'bg-rose-50 text-rose-700 ring-rose-100',
  confirmed: 'bg-sky-50 text-sky-700 ring-sky-100',
  cancelled: 'bg-slate-100 text-slate-600 ring-slate-200',
  pending: 'bg-amber-50 text-amber-700 ring-amber-100',
  approved: 'bg-emerald-50 text-emerald-700 ring-emerald-100',
  rejected: 'bg-rose-50 text-rose-700 ring-rose-100',
}

export function StatusBadge({ value }: { value: string }) {
  const cls = styles[value] ?? 'bg-slate-100 text-slate-600 ring-slate-200'
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ring-1 ${cls}`}>
      {value}
    </span>
  )
}
