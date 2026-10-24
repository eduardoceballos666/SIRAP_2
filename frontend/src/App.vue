<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'
import SirapLogo from '@/components/SirapLogo.vue'
import ToastStack from '@/components/ToastStack.vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
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
  <div v-else class="flex min-h-screen">
    <!-- Barra lateral -->
    <aside :class="menuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'"
           class="fixed inset-y-0 left-0 z-30 flex w-72 flex-col bg-navy-900 px-4 py-6 text-white transition-transform lg:sticky lg:top-0 lg:h-screen">
      <SirapLogo />
      <p class="mt-8 mb-2 px-2 text-xs font-semibold tracking-[.14em] text-slate-400">MÓDULOS</p>
      <nav class="flex flex-col gap-1.5">
        <RouterLink v-for="i in items" :key="i.to" :to="i.to"
                    class="flex items-center gap-3 rounded-xl px-4 py-3 text-[15px] text-slate-200 transition hover:bg-white/7"
                    active-class="!bg-brand-600 !text-white shadow-[inset_4px_0_0_#7fb0ff]">
          <AppIcon :name="i.icon" :size="22" /> <span>{{ i.label }}</span>
        </RouterLink>
      </nav>
      <div class="mt-auto rounded-xl bg-white/5 p-3 text-sm">
        <div class="flex items-center gap-2">
          <div class="grid h-9 w-9 place-items-center rounded-full bg-brand-600"><AppIcon name="user" :size="18" /></div>
          <div class="min-w-0">
            <p class="truncate font-semibold">{{ auth.user?.nombre }}</p>
            <p class="text-xs text-slate-400">{{ roleLabel[auth.user?.rol] }}</p>
          </div>
        </div>
        <button class="mt-3 flex w-full items-center justify-center gap-2 rounded-lg border border-white/15 py-2 text-slate-200 hover:bg-white/10" @click="logout">
          <AppIcon name="logout" :size="16" /> Cerrar sesión
        </button>
      </div>
    </aside>
    <div v-if="menuOpen" class="fixed inset-0 z-20 bg-black/40 lg:hidden" @click="menuOpen = false"></div>

    <!-- Contenido -->
    <main class="min-w-0 flex-1 px-4 py-5 sm:px-6 lg:px-8">
      <header class="mb-5 flex items-start justify-between gap-4">
        <div class="flex items-start gap-3">
          <button class="mt-1 rounded-lg bg-white p-2 shadow lg:hidden" aria-label="Abrir menú" @click="menuOpen = true">
            <AppIcon name="menu" />
          </button>
          <div>
            <p class="text-sm font-bold tracking-wide text-muted">SIRAP / SISTEMA DE ACCESO</p>
            <h1 class="text-2xl font-extrabold tracking-tight sm:text-3xl">{{ route.meta.title }}</h1>
          </div>
        </div>
        <p class="hidden pt-1 text-sm text-muted sm:block">{{ clock }}</p>
      </header>
      <RouterView />
    </main>
  </div>
  <ToastStack />
</template>
