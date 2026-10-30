import { defineStore } from 'pinia'
import { api } from '@/lib/api'
import { localeTag } from '@/i18n'

const THEME_KEY = 'sirap_theme'

function initialTheme() {
  try {
    const saved = localStorage.getItem(THEME_KEY)
    if (saved === 'dark' || saved === 'light') return saved
  } catch { /* sin almacenamiento */ }
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

// Estado del puesto de control: garita y movimiento elegidos, datos del sistema, tema, avisos y
// las lecturas hechas en esta sesión (para compararlas; no se guardan en el servidor hasta que se registran).
export const useSessionStore = defineStore('session', {
  state: () => ({
    system: null,
    garita: null,
    movimiento: 'ENTRADA',
    toasts: [],
    theme: initialTheme(),
    lecturas: [],
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
    applyTheme() {
      document.documentElement.classList.toggle('dark', this.theme === 'dark')
    },
    toggleTheme() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark'
      try { localStorage.setItem(THEME_KEY, this.theme) } catch { /* sin almacenamiento */ }
      this.applyTheme()
    },
    addLectura(lectura) {
      this.lecturas.unshift({ id: Date.now() + Math.random(), hora: new Date().toLocaleTimeString(localeTag.value), ...lectura })
      this.lecturas = this.lecturas.slice(0, 50)
    },
    markRegistered(id, accion) {
      const l = this.lecturas.find((x) => x.id === id)
      if (l) l.registro = accion
    },
    clearUnregisteredLecturas(ids) {
      const targets = new Set(ids)
      this.lecturas = this.lecturas.filter((l) => !targets.has(l.id) || l.registro)
    },
    clearLecturas() {
      this.lecturas = []
    },
  },
})
