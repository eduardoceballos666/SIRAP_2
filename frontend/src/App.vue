<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'
import SirapLogo from '@/components/SirapLogo.vue'
import ToastStack from '@/components/ToastStack.vue'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
import { language, localeTag, t } from '@/i18n'
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
  { to: '/administracion', label: 'Administración', icon: 'settings', roles: ['ADMINISTRADOR', 'SUPERVISOR'] },
  { to: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
].filter((i) => !i.roles || auth.hasRole(...i.roles)))

const clock = computed(() => now.value.toLocaleString(localeTag.value, { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }))
const isPublic = computed(() => route.meta.public)
const roleLabel = { OPERADOR: 'Operador', SUPERVISOR: 'Supervisor', ADMINISTRADOR: 'Administrador' }

watch([language, route], () => {
  document.title = `SIRAP · ${t(route.meta.title || (isPublic.value ? 'Iniciar sesión' : 'Control de acceso'))}`
}, { immediate: true })

function logout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div v-if="isPublic" class="public-shell">
    <LanguageSwitcher class="language-switcher-public" />
    <RouterView />
  </div>
  <div v-else class="app-shell">
    <aside class="app-topbar" :aria-label='$t("Navegación principal")'>
      <RouterLink to="/reconocimiento" class="sidebar-brand" :aria-label='$t("SIRAP: reconocimiento")'><SirapLogo /></RouterLink>
      <LanguageSwitcher />
      <nav class="top-navigation" :aria-label='$t("Módulos")'>
        <RouterLink v-for="i in items" :key="i.to" :to="i.to" active-class="selected"><AppIcon :name="i.icon" :size="19" /><span>{{ $t(i.label) }}</span></RouterLink>
      </nav>
      <div class="sidebar-bottom">
        <RouterLink to="/modelo" class="about-link" active-class="selected"><AppIcon name="info" :size="19" /><span>{{ $t("Acerca del modelo") }}</span></RouterLink>
        <div class="top-user">
          <span class="user-name" :title="$t(roleLabel[auth.user?.rol])">{{ auth.user?.nombre }} {{ $t("·") }} {{ $t(roleLabel[auth.user?.rol]) }}</span>
          <button :aria-label="$t(session.theme === 'dark' ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro')" @click="session.toggleTheme()"><AppIcon :name="session.theme === 'dark' ? 'sun' : 'moon'" :size="17" /></button>
          <button :title='$t("Cerrar sesión")' :aria-label='$t("Cerrar sesión")' @click="logout"><AppIcon name="logout" :size="17" /></button>
        </div>
      </div>
    </aside>
    <main class="app-content" :class="{ 'access-content': route.path === '/reconocimiento' }">
      <header v-if="route.path !== '/reconocimiento'" class="page-heading"><h1>{{ $t(route.meta.title) }}</h1><span>{{ clock }}</span></header>
      <RouterView />
    </main>
  </div>
  <ToastStack />
</template>
