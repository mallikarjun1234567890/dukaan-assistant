import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { AuthProvider, useAuth } from './context/AuthContext'
import { SHOP_HOME } from './lib/plans'
import { AdminDashboardPage } from './pages/AdminDashboardPage'
import { AdminLoginPage } from './pages/AdminLoginPage'
import { AIPage } from './pages/AIPage'
import { ChoosePlanPage } from './pages/ChoosePlanPage'
import { DashboardPage } from './pages/DashboardPage'
import { ForgotPasswordPage } from './pages/ForgotPasswordPage'
import { InventoryPage } from './pages/InventoryPage'
import { InvoiceDetailPage } from './pages/InvoiceDetailPage'
import { InvoicesPage } from './pages/InvoicesPage'
import { LandingPage } from './pages/LandingPage'
import { LoginPage } from './pages/LoginPage'
import { PrivacyPage } from './pages/PrivacyPage'
import { RegisterPage } from './pages/RegisterPage'
import { RegisterSuccessPage } from './pages/RegisterSuccessPage'
import { ReordersPage } from './pages/ReordersPage'
import { ResetPasswordPage } from './pages/ResetPasswordPage'
import { SettingsPage } from './pages/SettingsPage'
import { SubscriptionLockPage } from './pages/SubscriptionLockPage'
import { TermsPage } from './pages/TermsPage'
import type { ReactNode } from 'react'

function ShopProtected({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) {
    return <div className="p-8 text-sm text-slate-500">Checking session…</div>
  }
  if (!user) {
    return <Navigate to="/login" replace />
  }
  if (user.role === 'platform_admin') {
    return <Navigate to="/admin" replace />
  }
  if (user.shop_locked) {
    return <SubscriptionLockPage />
  }
  return children
}

function AdminProtected({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) {
    return <div className="p-8 text-sm text-slate-500">Checking session…</div>
  }
  if (!user) {
    return <Navigate to="/admin/login" replace />
  }
  if (user.role !== 'platform_admin') {
    return <Navigate to={SHOP_HOME} replace />
  }
  return children
}

function GuestHome() {
  const { user, loading } = useAuth()
  if (loading) {
    return <div className="p-8 text-sm text-slate-500">Checking session…</div>
  }
  if (user?.role === 'platform_admin') {
    return <Navigate to="/admin" replace />
  }
  if (user) {
    return <Navigate to={SHOP_HOME} replace />
  }
  return <LandingPage />
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<GuestHome />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/register/success" element={<RegisterSuccessPage />} />
      <Route path="/choose-plan" element={<ChoosePlanPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/terms" element={<TermsPage />} />
      <Route path="/privacy" element={<PrivacyPage />} />
      <Route path="/admin/login" element={<AdminLoginPage />} />
      <Route
        path="/admin"
        element={
          <AdminProtected>
            <AdminDashboardPage />
          </AdminProtected>
        }
      />
      <Route
        element={
          <ShopProtected>
            <Layout />
          </ShopProtected>
        }
      >
        <Route path={SHOP_HOME} element={<DashboardPage />} />
        <Route path="/inventory" element={<InventoryPage />} />
        <Route path="/invoices" element={<InvoicesPage />} />
        <Route path="/invoices/:invoiceId" element={<InvoiceDetailPage />} />
        <Route path="/reorders" element={<ReordersPage />} />
        <Route path="/ai" element={<AIPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  )
}
