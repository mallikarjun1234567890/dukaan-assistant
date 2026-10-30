import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { api } from '../services/api'
import type { RegisterPayload, User } from '../types'

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  adminLogin: (email: string, password: string) => Promise<void>
  register: (payload: RegisterPayload) => Promise<void>
  logout: () => Promise<void>
  refresh: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    api
      .me()
      .then((current) => {
        if (active) setUser(current)
      })
      .catch(() => {
        if (active) setUser(null)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      login: async (email, password) => {
        await api.csrf().catch(() => undefined)
        const result = await api.login(email, password)
        setUser(result.user)
      },
      adminLogin: async (email, password) => {
        await api.csrf().catch(() => undefined)
        const result = await api.adminLogin(email, password)
        setUser(result.user)
      },
      register: async (payload) => {
        await api.csrf().catch(() => undefined)
        const result = await api.register({
          email: payload.email,
          password: payload.password,
          shop_name: payload.shop_name,
          owner_name: payload.owner_name,
          phone: payload.phone,
          plan_preference: payload.plan_preference ?? 'trial',
        })
        setUser(result.user)
        if (payload.shop_photo) {
          try {
            await api.upload(payload.shop_photo, 'shop_logo')
          } catch {
            // Shop already exists; owner can retry the photo in Settings.
          }
        }
        if (payload.owner_photo) {
          try {
            await api.upload(payload.owner_photo, 'avatar')
            const current = await api.me()
            setUser(current)
          } catch {
            // Same: profile photo can be added later in Settings.
          }
        }
      },
      logout: async () => {
        try {
          await api.logout()
        } finally {
          setUser(null)
        }
      },
      refresh: async () => {
        const current = await api.me()
        setUser(current)
      },
    }),
    [user, loading],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return context
}
