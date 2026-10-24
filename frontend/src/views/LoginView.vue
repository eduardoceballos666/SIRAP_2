<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SirapLogo from '@/components/SirapLogo.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const usuario = ref('operador')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(usuario.value, password.value)
    router.push(route.query.next || '/reconocimiento')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="grid min-h-screen place-items-center bg-navy-900 p-4">
    <div class="w-full max-w-md">
      <SirapLogo class="mb-6" />
      <form class="card space-y-4" @submit.prevent="submit">
        <h1 class="text-xl font-bold">Iniciar sesión</h1>
        <div>
          <label class="field-label" for="u">Usuario</label>
          <input id="u" v-model.trim="usuario" class="field" autocomplete="username" required />
        </div>
        <div>
          <label class="field-label" for="p">Contraseña</label>
          <input id="p" v-model="password" type="password" class="field" autocomplete="current-password" required />
        </div>
        <p v-if="error" class="rounded-lg bg-bad-soft px-3 py-2 text-sm font-semibold text-bad">{{ error }}</p>
        <button class="btn-primary w-full" :disabled="loading">{{ loading ? 'Ingresando…' : 'Ingresar' }}</button>
        <p class="text-xs text-muted">
          Usuarios de demostración: <b>operador</b>, <b>supervisor</b> y <b>admin</b>. La contraseña de demostración
          se define con <code>SIRAP_DEMO_PASSWORD</code> en el servidor.
        </p>
      </form>
    </div>
  </div>
</template>
