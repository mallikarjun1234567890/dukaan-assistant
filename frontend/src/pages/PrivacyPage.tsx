import { Link } from 'react-router-dom'
import { BrandMark } from '../components/BrandMark'
import { PublicFooter } from '../components/PublicFooter'

export function PrivacyPage() {
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
        <h1 className="mt-2 text-3xl font-extrabold text-slate-900">Privacy policy</h1>
        <p className="mt-4 text-sm text-slate-500">What this application stores and who can see it.</p>
        <div className="mt-8 space-y-5 text-sm leading-7 text-slate-700">
          <p>
            Shop registration stores the shop name, owner name, phone, email, and a password hash. Sign-in uses an
            HttpOnly session cookie. CSRF tokens protect state-changing requests.
          </p>
          <p>
            Inventory, invoices, reorder history, shop settings, and AI prompts are scoped to your shop. Another
            shop owner should not be able to read those records. Platform administrators use a separate login and
            do not use the shop dashboard as an owner.
          </p>
          <p>
            Optional shop and owner photos are uploaded through the backend to Cloudinary. The Cloudinary API
            secret stays on the server. Email (welcome, password reset, payment receipt) is sent through Resend
            when it is configured. A failed email does not undo registration.
          </p>
          <p>
            AI providers receive the question plus the authenticated shop context needed to answer it. Do not
            paste unrelated personal data into the assistant.
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
