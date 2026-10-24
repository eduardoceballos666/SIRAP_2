<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'
import SirapLogo from '@/components/SirapLogo.vue'
import ToastStack from '@/components/ToastStack.vue'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const session = useSessionStore()
const now = ref(new Date())
let timer
onMounted(() => { timer = setInterval(() => (now.value = new Date()), 1000) })
onBeforeUnmount(() => clearInterval(timer))

const items = computed(() => [
  { to: '/reconocimiento', label: 'Reconocimiento y Acceso', icon: 'scan' },
  { to: '/historial', label: 'Historial', icon: 'history' },
  { to: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
  { to: '/administracion', label: 'Administración', icon: 'settings', roles: ['ADMINISTRADOR', 'SUPERVISOR'] },
].filter((i) => !i.roles || auth.hasRole(...i.roles)))

const clock = computed(() => now.value.toLocaleString('es-EC', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }))
const isPublic = computed(() => route.meta.public)
const roleLabel = { OPERADOR: 'Operador', SUPERVISOR: 'Supervisor', ADMINISTRADOR: 'Administrador' }

function logout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <RouterView v-if="isPublic" />
  <div v-else class="app-shell">
    <aside class="app-topbar" aria-label="Navegación principal">
      <RouterLink to="/reconocimiento" class="sidebar-brand" aria-label="SIRAP: reconocimiento"><SirapLogo /></RouterLink>
      <nav class="top-navigation" aria-label="Módulos">
        <RouterLink v-for="i in items" :key="i.to" :to="i.to" active-class="selected"><AppIcon :name="i.icon" :size="19" /><span>{{ i.label }}</span></RouterLink>
      </nav>
      <div class="sidebar-bottom">
        <div class="top-user">
          <span class="user-name" :title="roleLabel[auth.user?.rol]">{{ auth.user?.nombre }} · {{ roleLabel[auth.user?.rol] }}</span>
          <button :aria-label="session.theme === 'dark' ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'" @click="session.toggleTheme()"><AppIcon :name="session.theme === 'dark' ? 'sun' : 'moon'" :size="17" /></button>
          <button title="Cerrar sesión" aria-label="Cerrar sesión" @click="logout"><AppIcon name="logout" :size="17" /></button>
        </div>
        <RouterLink to="/modelo" class="about-link" active-class="selected"><AppIcon name="info" :size="19" /><span>Acerca del modelo</span></RouterLink>
      </div>
    </aside>
    <main class="app-content" :class="{ 'access-content': route.path === '/reconocimiento' }">
      <header v-if="route.path !== '/reconocimiento'" class="page-heading"><h1>{{ route.meta.title }}</h1><span>{{ clock }}</span></header>
      <RouterView />
    </main>
  </div>
  <ToastStack />
</template>
