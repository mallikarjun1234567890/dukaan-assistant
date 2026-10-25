import {
  BadgeCheck,
  Bell,
  Bot,
  ChevronDown,
  LayoutDashboard,
  Menu,
  Package,
  Receipt,
  RefreshCw,
  Settings,
  X,
} from 'lucide-react'
import { useEffect, useId, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { BrandMark } from '../components/BrandMark'
import { PublicFooter } from '../components/PublicFooter'
import { PLANS, registerPath, type PlanId } from '../lib/plans'

const NAV = [
  { href: '#features', label: 'Features' },
  { href: '#how-it-works', label: 'How it works' },
  { href: '#pricing', label: 'Pricing' },
  { href: '#faq', label: 'FAQ' },
] as const

const FEATURES = [
  {
    title: 'Inventory management',
    text: 'Add products with SKU, category, selling price, purchase cost, stock, minimum level, and supplier. Search and filter by category or stock status.',
    icon: Package,
  },
  {
    title: 'Invoice generation',
    text: 'Create invoices from your catalog, preview and print them, and keep a history of confirmed sales. Totals are calculated on the server.',
    icon: Receipt,
  },
  {
    title: 'Low-stock alerts',
    text: 'See how many items are at or below the minimum on the dashboard, and mark stock as out, low, or healthy in inventory.',
    icon: Bell,
  },
  {
    title: 'Smart reorder recommendations',
    text: 'Review suggested restock quantities and estimated cost. Approve or reject internally — this does not place a supplier order.',
    icon: RefreshCw,
  },
  {
    title: 'Sales dashboard',
    text: 'Track product count, inventory value, low-stock count, today’s confirmed sales, recent invoices, and a stock-level chart.',
    icon: LayoutDashboard,
  },
  {
    title: 'AI shop assistant',
    text: 'Ask questions about your own inventory and sales. Answers stay grounded in the signed-in shop. Exact numbers are calculated in the backend.',
    icon: Bot,
  },
  {
    title: 'Shop settings',
    text: 'Update shop name, phone, timezone, opening hours, weekly off-day, and shop or owner photos. Images are uploaded through the backend.',
    icon: Settings,
  },
] as const

const STEPS = [
  {
    step: '1',
    title: 'Register your shop',
    text: 'Choose a trial or monthly plan, then create one shop and one owner account. The server starts the trial clock.',
  },
  {
    step: '2',
    title: 'Add products and manage sales',
    text: 'Build your catalog, create invoices, and keep stock in sync as confirmed sales deduct inventory.',
  },
  {
    step: '3',
    title: 'Get inventory insights and AI assistance',
    text: 'Use the dashboard, reorder list, and shop AI to decide what to restock — without leaving your shop data.',
  },
] as const

const FAQS = [
  {
    q: 'What do I get during the free trial?',
    a: 'The same shop tools as the monthly plan: inventory, invoices, dashboard, reorder recommendations, AI assistant, and settings. The trial lasts 30 days from the moment the server creates your shop.',
  },
  {
    q: 'What happens after 30 days?',
    a: 'An expired trial locks inventory, invoices, and AI. You can still open settings and subscribe. After a grace period, the shop may be removed. Subscribe before that if you want to keep the data.',
  },
  {
    q: 'Is the ₹499 plan charged automatically every month?',
    a: 'Not yet. The product is sold as a monthly plan, but checkout is a Razorpay test payment. The live test charge is ₹1. Paid access is turned on only after the backend verifies the payment signature. Recurring billing is not implemented.',
  },
  {
    q: 'Can another shop see my inventory or invoices?',
    a: 'No. Each registration creates an isolated shop. Owners only see records for their own shop. Platform administration uses a separate login.',
  },
  {
    q: 'Do I need a mobile app?',
    a: 'No. Dukaan Assistant is a responsive web app. Sign in from a phone, tablet, or desktop browser.',
  },
] as const

export function LandingPage() {
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    const id = location.hash.replace('#', '')
    if (!id) return
    document.getElementById(id)?.scrollIntoView({ block: 'start' })
  }, [location.hash])

  useEffect(() => {
    setMenuOpen(false)
  }, [location.hash, location.pathname])

  return (
    <div className="min-h-screen bg-[#f3f6f5]">
      <a href="#main" className="skip-link sr-only">
        Skip to content
      </a>

      <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
          <BrandMark />
          <nav className="hidden items-center gap-6 lg:flex" aria-label="Page">
            {NAV.map((item) => (
              <a key={item.href} href={item.href} className="text-sm font-medium text-slate-600 hover:text-teal-800">
                {item.label}
              </a>
            ))}
          </nav>
          <div className="hidden items-center gap-3 lg:flex">
            <Link to="/login" className="rounded-xl px-3 py-2 text-sm font-semibold text-teal-800 hover:bg-teal-50">
              Sign in
            </Link>
            <Link
              to={registerPath('trial')}
              className="rounded-xl bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800"
            >
              Get started
            </Link>
          </div>
          <button
            type="button"
            className="rounded-lg p-2 text-slate-700 hover:bg-slate-100 lg:hidden"
            aria-expanded={menuOpen}
            aria-controls="mobile-nav"
            onClick={() => setMenuOpen((open) => !open)}
          >
            <span className="sr-only">{menuOpen ? 'Close menu' : 'Open menu'}</span>
            {menuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
        {menuOpen ? (
          <div id="mobile-nav" className="border-t border-slate-200 px-4 py-4 lg:hidden">
            <nav className="flex flex-col gap-2" aria-label="Mobile">
              {NAV.map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  className="rounded-xl px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
                  onClick={() => setMenuOpen(false)}
                >
                  {item.label}
                </a>
              ))}
              <Link to="/login" className="rounded-xl px-3 py-2 text-sm font-semibold text-teal-800 hover:bg-teal-50">
                Sign in
              </Link>
              <Link
                to={registerPath('trial')}
                className="rounded-xl bg-teal-700 px-3 py-2 text-center text-sm font-semibold text-white hover:bg-teal-800"
              >
                Get started
              </Link>
            </nav>
          </div>
        ) : null}
      </header>

      <main id="main">
        <section className="relative overflow-hidden bg-[#0b3b36] text-white">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(45,212,191,0.18),transparent_36%)]" />
          <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-4 py-16 sm:px-6 lg:grid-cols-[1.15fr_0.85fr] lg:px-8 lg:py-24">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal-200">Dukaan Assistant</p>
              <h1 className="mt-4 max-w-xl text-4xl font-extrabold leading-tight sm:text-5xl">
                Run your shop smarter with AI.
              </h1>
              <p className="mt-5 max-w-xl text-lg text-teal-50/90">
                Manage inventory, generate invoices, track sales, and make smarter restocking decisions from one
                simple dashboard.
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Link
                  to={registerPath('trial')}
                  className="inline-flex items-center justify-center rounded-xl bg-amber-400 px-5 py-3 text-sm font-bold text-[#0b3b36] hover:bg-amber-300"
                >
                  Start free trial
                </Link>
                <a
                  href="#features"
                  className="inline-flex items-center justify-center rounded-xl border border-white/25 px-5 py-3 text-sm font-semibold text-white hover:bg-white/10"
                >
                  Explore features
                </a>
              </div>
              <p className="mt-6 text-sm text-teal-100/80">
                30-day trial · one shop per registration · no invented customer counts
              </p>
            </div>
            <div className="rounded-3xl bg-white/8 p-6 ring-1 ring-white/15">
              <p className="text-sm font-semibold text-amber-300">What you can do today</p>
              <ul className="mt-4 space-y-3 text-sm text-teal-50">
                {[
                  'Keep stock, prices, and suppliers in one catalog',
                  'Confirm sales and print invoices',
                  'See what is running low before you run out',
                  'Ask the shop AI about your own numbers',
                ].map((item) => (
                  <li key={item} className="flex gap-3">
                    <BadgeCheck className="mt-0.5 shrink-0 text-amber-300" size={18} aria-hidden="true" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        <section id="features" className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-teal-700">Features</p>
          <h2 className="mt-2 text-3xl font-extrabold text-slate-900">Built around the shop work you already do</h2>
          <p className="mt-3 max-w-2xl text-slate-600">
            These cards describe tools that are in the product now. They do not promise forecasts, supplier
            integrations, or multi-staff logins that are not implemented.
          </p>
          <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {FEATURES.map((feature) => {
              const Icon = feature.icon
              return (
                <article key={feature.title} className="rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-teal-50 text-teal-700">
                    <Icon size={20} aria-hidden="true" />
                  </div>
                  <h3 className="mt-4 text-lg font-bold text-slate-900">{feature.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{feature.text}</p>
                </article>
              )
            })}
          </div>
        </section>

        <section id="how-it-works" className="bg-white">
          <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-teal-700">How it works</p>
            <h2 className="mt-2 text-3xl font-extrabold text-slate-900">Three steps from empty shop to daily use</h2>
            <ol className="mt-10 grid gap-4 md:grid-cols-3">
              {STEPS.map((item) => (
                <li key={item.step} className="rounded-3xl bg-[#f3f6f5] p-6 ring-1 ring-slate-200">
                  <p className="text-sm font-bold text-amber-600">Step {item.step}</p>
                  <h3 className="mt-2 text-xl font-bold text-slate-900">{item.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{item.text}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section id="pricing" className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-teal-700">Pricing</p>
          <h2 className="mt-2 text-3xl font-extrabold text-slate-900">Start on a trial, or subscribe now</h2>
          <p className="mt-3 max-w-2xl text-slate-600">
            Both options include the same shop features. Choose a plan first, then register. Prices below are the
            advertised plan amounts — checkout still runs in Razorpay test mode.
          </p>
          <div className="mt-10 grid gap-6 lg:grid-cols-2">
            <PricingCard plan="trial" />
            <PricingCard plan="monthly" featured />
          </div>
        </section>

        <section id="security" className="bg-[#0b3b36] text-white">
          <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-teal-200">Security and privacy</p>
            <h2 className="mt-2 text-3xl font-extrabold">Your shop stays your shop</h2>
            <div className="mt-8 grid gap-4 md:grid-cols-3">
              <article className="rounded-3xl bg-white/8 p-6 ring-1 ring-white/10">
                <h3 className="font-bold">Isolated tenant data</h3>
                <p className="mt-2 text-sm leading-6 text-teal-50/90">
                  Products, invoices, reorders, settings, and AI context are scoped to the signed-in shop.
                </p>
              </article>
              <article className="rounded-3xl bg-white/8 p-6 ring-1 ring-white/10">
                <h3 className="font-bold">Session cookies</h3>
                <p className="mt-2 text-sm leading-6 text-teal-50/90">
                  Sign-in uses an HttpOnly JWT cookie and CSRF checks on state-changing requests. Passwords are
                  hashed with Argon2.
                </p>
              </article>
              <article className="rounded-3xl bg-white/8 p-6 ring-1 ring-white/10">
                <h3 className="font-bold">Uploads and email</h3>
                <p className="mt-2 text-sm leading-6 text-teal-50/90">
                  Images go through the backend to Cloudinary. Welcome and receipt emails are best-effort and do
                  not block shop creation.
                </p>
              </article>
            </div>
          </div>
        </section>

        <section id="faq" className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-teal-700">FAQ</p>
          <h2 className="mt-2 text-3xl font-extrabold text-slate-900">Questions we can answer from the current product</h2>
          <div className="mt-8 space-y-3">
            {FAQS.map((item) => (
              <FaqItem key={item.q} question={item.q} answer={item.a} />
            ))}
          </div>
        </section>
      </main>

      <PublicFooter light />
    </div>
  )
}

function PricingCard({ plan, featured = false }: { plan: PlanId; featured?: boolean }) {
  const data = PLANS[plan]
  return (
    <article
      className={`flex flex-col rounded-3xl p-6 shadow-sm ring-1 ${
        featured ? 'bg-[#0b3b36] text-white ring-teal-900' : 'bg-white text-slate-900 ring-slate-200'
      }`}
    >
      <p className={`text-sm font-semibold ${featured ? 'text-amber-300' : 'text-teal-700'}`}>{data.name}</p>
      <div className="mt-3 flex items-end gap-2">
        <span className="text-4xl font-extrabold">{data.price}</span>
        <span className={`pb-1 text-sm ${featured ? 'text-teal-100' : 'text-slate-500'}`}>{data.period}</span>
      </div>
      <p className={`mt-3 text-sm ${featured ? 'text-teal-50' : 'text-slate-600'}`}>{data.summary}</p>
      <ul className="mt-6 flex-1 space-y-2 text-sm">
        {data.features.map((feature) => (
          <li key={feature} className="flex gap-2">
            <BadgeCheck
              size={16}
              className={`mt-0.5 shrink-0 ${featured ? 'text-amber-300' : 'text-teal-700'}`}
              aria-hidden="true"
            />
            <span>{feature}</span>
          </li>
        ))}
      </ul>
      <ul className={`mt-4 space-y-1 text-xs ${featured ? 'text-teal-100/80' : 'text-slate-500'}`}>
        {data.notes.map((note) => (
          <li key={note}>{note}</li>
        ))}
      </ul>
      <Link
        to={registerPath(plan)}
        className={`mt-6 inline-flex items-center justify-center rounded-xl px-4 py-3 text-sm font-bold ${
          featured
            ? 'bg-amber-400 text-[#0b3b36] hover:bg-amber-300'
            : 'bg-teal-700 text-white hover:bg-teal-800'
        }`}
      >
        {data.cta}
      </Link>
    </article>
  )
}

function FaqItem({ question, answer }: { question: string; answer: string }) {
  const panelId = useId()
  const [open, setOpen] = useState(false)
  return (
    <div className="rounded-2xl bg-white ring-1 ring-slate-200">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left text-sm font-semibold text-slate-900"
      >
        <span>{question}</span>
        <ChevronDown size={18} className={`shrink-0 text-teal-700 transition ${open ? 'rotate-180' : ''}`} />
      </button>
      {open ? (
        <p id={panelId} className="px-5 pb-4 text-sm leading-6 text-slate-600">
          {answer}
        </p>
      ) : null}
    </div>
  )
}
