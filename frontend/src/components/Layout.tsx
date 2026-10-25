import {
  LayoutDashboard,
  LogOut,
  Menu,
  Package,
  Receipt,
  RefreshCw,
  Settings,
  Sparkles,
  Store,
  X,
} from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { formatDate } from '../services/api'

function trialDaysLeft(iso?: string | null): number | null {
  if (!iso) return null
  const ms = new Date(iso).getTime() - Date.now()
  return Math.ceil(ms / (1000 * 60 * 60 * 24))
}

const links = [
  { to: '/app', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/inventory', label: 'Inventory', icon: Package },
  { to: '/invoices', label: 'Invoices and Sales', icon: Receipt },
  { to: '/reorders', label: 'Reorder Recommendations', icon: RefreshCw },
  { to: '/ai', label: 'Ask Dukaan AI', icon: Sparkles },
  { to: '/settings', label: 'Shop settings', icon: Settings },
]

export function Layout() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const daysLeft = trialDaysLeft(user?.trial_ends_at)
  const showTrialBanner = user?.plan === 'trial' && daysLeft != null && daysLeft <= 5

  const nav = (
    <nav className="flex flex-1 flex-col gap-1">
      {links.map((link) => {
        const Icon = link.icon
        return (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === '/app'}
            onClick={() => setOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                isActive ? 'bg-white/12 text-white' : 'text-teal-100 hover:bg-white/8 hover:text-white'
              }`
            }
          >
            <Icon size={18} />
            {link.label}
          </NavLink>
        )
      })}
    </nav>
  )

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[260px_1fr]">
      <aside className="no-print hidden flex-col bg-[#0b3b36] px-4 py-5 text-white lg:flex">
        <div className="mb-8 flex items-center gap-3 px-2">
          {user?.avatar_url ? (
            <img src={user.avatar_url} alt="" className="h-10 w-10 rounded-xl object-cover" />
          ) : (
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-400 text-[#0b3b36]">
              <Store size={20} />
            </div>
          )}
          <div>
            <p className="text-sm font-bold">Dukaan Assistant</p>
            <p className="text-xs text-teal-200">{user?.shop_name}</p>
          </div>
        </div>
        {nav}
        <button
          type="button"
          onClick={() => void logout()}
          className="mt-6 flex items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-teal-100 hover:bg-white/8 hover:text-white"
        >
          <LogOut size={18} />
          Logout
        </button>
      </aside>

      <div className="min-w-0">
        <header className="no-print sticky top-0 z-20 flex items-center justify-between border-b border-slate-200 bg-white/90 px-4 py-3 backdrop-blur lg:hidden">
          <div className="flex items-center gap-2 font-semibold text-teal-800">
            <Store size={18} />
            Dukaan
          </div>
          <button
            type="button"
            className="rounded-lg p-2 text-slate-600 hover:bg-slate-100"
            onClick={() => setOpen((value) => !value)}
            aria-label={open ? 'Close menu' : 'Open menu'}
          >
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
        </header>
        {open ? (
          <div className="no-print fixed inset-0 z-30 bg-[#0b3b36] p-4 lg:hidden">
            <div className="mb-6 flex items-center justify-between text-white">
              <span className="font-semibold">Menu</span>
              <button type="button" onClick={() => setOpen(false)} aria-label="Close menu">
                <X />
              </button>
            </div>
            {nav}
            <button
              type="button"
              onClick={() => void logout()}
              className="mt-6 flex items-center gap-3 text-sm text-teal-100"
            >
              <LogOut size={18} />
              Logout
            </button>
          </div>
        ) : null}
        <main className="px-4 py-6 sm:px-6 lg:px-8">
          {showTrialBanner ? (
            <div className="mb-4 rounded-2xl bg-amber-50 px-4 py-3 text-sm text-amber-900 ring-1 ring-amber-200">
              Trial ends {user?.trial_ends_at ? formatDate(user.trial_ends_at) : 'soon'} — {daysLeft} day(s)
              left. Subscribe ₹499/month from Settings (test charge ₹1).
            </div>
          ) : null}
          <Outlet />
        </main>
      </div>
    </div>
  )
}
