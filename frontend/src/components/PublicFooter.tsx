import { Link } from 'react-router-dom'
import { BrandMark } from './BrandMark'

export function PublicFooter({ light = false }: { light?: boolean }) {
  const linkClass = light
    ? 'text-teal-100 hover:text-white hover:underline'
    : 'text-slate-600 hover:text-teal-800 hover:underline'

  return (
    <footer className={light ? 'bg-[#082824] text-teal-100' : 'border-t border-slate-200 bg-white text-slate-600'}>
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-12 sm:px-6 md:grid-cols-4 lg:px-8">
        <div className="md:col-span-2">
          <BrandMark light={light} />
          <p className={`mt-4 max-w-md text-sm ${light ? 'text-teal-100/80' : 'text-slate-500'}`}>
            Multi-tenant shop software for inventory, invoices, restocking, and an AI assistant grounded in your
            own data.
          </p>
        </div>
        <div>
          <p className={`text-sm font-semibold ${light ? 'text-white' : 'text-slate-900'}`}>Product</p>
          <ul className="mt-3 space-y-2 text-sm">
            <li>
              <Link className={linkClass} to="/#features">
                Features
              </Link>
            </li>
            <li>
              <Link className={linkClass} to="/#pricing">
                Pricing
              </Link>
            </li>
            <li>
              <Link className={linkClass} to="/login">
                Sign in
              </Link>
            </li>
            <li>
              <Link className={linkClass} to="/register?plan=trial">
                Get started
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <p className={`text-sm font-semibold ${light ? 'text-white' : 'text-slate-900'}`}>Legal and contact</p>
          <ul className="mt-3 space-y-2 text-sm">
            <li>
              <Link className={linkClass} to="/terms">
                Terms
              </Link>
            </li>
            <li>
              <Link className={linkClass} to="/privacy">
                Privacy policy
              </Link>
            </li>
            <li>
              <Link className={linkClass} to="/login">
                Contact via sign in
              </Link>
            </li>
          </ul>
        </div>
      </div>
      <div className={`border-t px-4 py-4 text-center text-xs sm:px-6 ${light ? 'border-white/10 text-teal-200/70' : 'border-slate-200 text-slate-400'}`}>
        Each shop account is isolated. Do not share demo credentials on a public network.
      </div>
    </footer>
  )
}
