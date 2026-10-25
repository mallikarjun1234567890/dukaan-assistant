import { Store } from 'lucide-react'
import { Link } from 'react-router-dom'

export function BrandMark({
  to = '/',
  light = false,
}: {
  to?: string
  light?: boolean
}) {
  return (
    <Link to={to} className="inline-flex items-center gap-3 rounded-xl focus-visible:outline-offset-4">
      <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-400 text-[#0b3b36]">
        <Store size={20} aria-hidden="true" />
      </span>
      <span className={`text-lg font-bold ${light ? 'text-white' : 'text-slate-900'}`}>Dukaan Assistant</span>
    </Link>
  )
}
