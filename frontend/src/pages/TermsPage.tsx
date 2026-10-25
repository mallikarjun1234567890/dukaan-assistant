import { Link } from 'react-router-dom'
import { BrandMark } from '../components/BrandMark'
import { PublicFooter } from '../components/PublicFooter'

export function TermsPage() {
  return (
    <div className="min-h-screen bg-[#f3f6f5]">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4 sm:px-6">
          <BrandMark />
          <Link to="/login" className="text-sm font-semibold text-teal-800 hover:underline">
            Sign in
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
        <p className="text-sm font-semibold text-teal-700">Legal</p>
        <h1 className="mt-2 text-3xl font-extrabold text-slate-900">Terms of use</h1>
        <p className="mt-4 text-sm text-slate-500">This page describes how this instance of Dukaan Assistant works today.</p>
        <div className="mt-8 space-y-5 text-sm leading-7 text-slate-700">
          <p>
            Registering creates one shop and one owner account. You are responsible for the products, invoices,
            and settings you store. Do not use another shop’s credentials.
          </p>
          <p>
            The free trial lasts 30 days from the server timestamp at registration. The advertised monthly price
            is ₹499. Checkout currently runs in Razorpay test mode with a ₹1 test charge. A frontend success
            message is not enough to activate paid access — the backend must verify the payment.
          </p>
          <p>
            Automatic recurring billing is not implemented. Approving a reorder records an internal request only.
            It does not order from a supplier or take payment.
          </p>
          <p>
            After a trial or paid period expires, shop tools lock. After a grace period the shop may be removed.
            Keep a local copy of anything you cannot afford to lose.
          </p>
        </div>
        <p className="mt-8 text-sm">
          <Link to="/" className="font-semibold text-teal-700 hover:underline">
            Back to home
          </Link>
        </p>
      </main>
      <PublicFooter />
    </div>
  )
}
