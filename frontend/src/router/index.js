import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { setUnauthorizedHandler } from '@/lib/api'

const routes = [
  { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { public: true, title: 'Iniciar sesión' } },
  { path: '/', redirect: '/reconocimiento' },
  { path: '/reconocimiento', name: 'recognition', component: () => import('@/views/RecognitionView.vue'),
    meta: { title: 'Reconocimiento automático y control de acceso' } },
  { path: '/dashboard', name: 'dashboard', component: () => import('@/views/DashboardView.vue'),
    meta: { title: 'Dashboard de operaciones' } },
  { path: '/historial', name: 'history', component: () => import('@/views/HistoryView.vue'),
    meta: { title: 'Historial de operaciones' } },
  { path: '/administracion', name: 'admin', component: () => import('@/views/AdminView.vue'),
    meta: { title: 'Administración', roles: ['ADMINISTRADOR', 'SUPERVISOR'] } },
  { path: '/modelo', name: 'about', component: () => import('@/views/AboutView.vue'),
    meta: { title: 'Acerca del modelo' } },
  { path: '/:pathMatch(.*)*', redirect: '/reconocimiento' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.meta.public) return auth.isAuthenticated && to.name === 'login' ? '/reconocimiento' : true
  if (!auth.isAuthenticated) return { name: 'login', query: { next: to.fullPath } }
  try {
    await auth.fetchMe()
  } catch {
    auth.logout()
    return { name: 'login' }
  }
  if (to.meta.roles && !auth.hasRole(...to.meta.roles)) return '/reconocimiento'
  document.title = `SIRAP · ${to.meta.title || 'Control de acceso'}`
  return true
})

setUnauthorizedHandler(() => {
  useAuthStore().logout()
  router.push({ name: 'login' })
})

export default router
