import { defineStore } from 'pinia'
import { api, getToken, setToken } from '@/lib/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({ token: getToken(), user: null }),
  getters: {
    isAuthenticated: (s) => Boolean(s.token),
    role: (s) => s.user?.rol,
  },
  actions: {
    async login(usuario, password) {
      const data = await api('/api/auth/login', { method: 'POST', body: { usuario, password } })
      this.token = data.access_token
      this.user = data.user
      setToken(this.token)
    },
    async fetchMe() {
      if (!this.token || this.user) return
      this.user = await api('/api/auth/me')
    },
    logout() {
      this.token = null
      this.user = null
      setToken(null)
    },
    hasRole(...roles) {
      return roles.includes(this.user?.rol)
    },
  },
})
