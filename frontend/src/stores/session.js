import { defineStore } from 'pinia'
import { api } from '@/lib/api'

// Estado del puesto de control: garita y tipo de movimiento elegidos, datos del sistema y avisos.
export const useSessionStore = defineStore('session', {
  state: () => ({
    system: null,
    garita: null,
    movimiento: 'ENTRADA',
    toasts: [],
  }),
  actions: {
    async loadSystem(force = false) {
      if (this.system && !force) return this.system
      this.system = await api('/api/system')
      if (!this.garita || !this.system.garitas.includes(this.garita)) {
        this.garita = this.system.garitas.find((g) => g.includes('3')) || this.system.garitas[0] || null
      }
      return this.system
    },
    notify(message, kind = 'ok') {
      const id = Date.now() + Math.random()
      this.toasts.push({ id, message, kind })
      setTimeout(() => { this.toasts = this.toasts.filter((t) => t.id !== id) }, 4500)
    },
  },
})
