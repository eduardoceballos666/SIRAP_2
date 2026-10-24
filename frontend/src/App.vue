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
const menuOpen = ref(false)
const now = ref(new Date())
let timer
onMounted(() => { timer = setInterval(() => (now.value = new Date()), 1000) })
onBeforeUnmount(() => clearInterval(timer))
watch(() => route.fullPath, () => (menuOpen.value = false))

const items = computed(() => [
  { to: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
  { to: '/reconocimiento', label: 'Reconocimiento y Acceso', icon: 'scan' },
  { to: '/historial', label: 'Historial', icon: 'history' },
  { to: '/administracion', label: 'Administración', icon: 'settings', roles: ['ADMINISTRADOR', 'SUPERVISOR'] },
  { to: '/modelo', label: 'Acerca del modelo', icon: 'info' },
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
    <header class="app-topbar">
      <RouterLink to="/reconocimiento" class="compact-logo" aria-label="SIRAP: reconocimiento"><SirapLogo /></RouterLink>
      <button class="mobile-menu" aria-label="Abrir menú" :aria-expanded="menuOpen" @click="menuOpen = !menuOpen"><AppIcon name="menu" /></button>
      <nav class="top-navigation" :class="{ 'is-open': menuOpen }" aria-label="Módulos">
        <RouterLink v-for="i in items" :key="i.to" :to="i.to" active-class="selected"><AppIcon :name="i.icon" :size="17" /><span>{{ i.label }}</span></RouterLink>
      </nav>
      <div class="top-user">
        <span class="user-name" :title="roleLabel[auth.user?.rol]">{{ auth.user?.nombre }}</span>
        <button :aria-label="session.theme === 'dark' ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'" @click="session.toggleTheme()"><AppIcon :name="session.theme === 'dark' ? 'sun' : 'moon'" :size="18" /></button>
        <button title="Cerrar sesión" aria-label="Cerrar sesión" @click="logout"><AppIcon name="logout" :size="18" /></button>
      </div>
    </header>
    <main class="app-content" :class="{ 'access-content': route.path === '/reconocimiento' }">
      <header class="page-heading"><h1>{{ route.meta.title }}</h1><span>{{ clock }}</span></header>
      <RouterView />
    </main>
  </div>
  <ToastStack />
</template>
