import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { SHOP_HOME } from '../lib/plans'

export function ChoosePlanPage() {
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
  return <Navigate to="/#pricing" replace />
}
