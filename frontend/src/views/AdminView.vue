<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import { api } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'

const auth = useAuthStore()
const session = useSessionStore()
const isAdmin = computed(() => auth.hasRole('ADMINISTRADOR'))
const TABS = [['vehiculos', 'Vehículos'], ['autorizaciones', 'Listas'], ['propietarios', 'Propietarios'], ['garitas', 'Garitas'], ['usuarios', 'Usuarios'], ['demo', 'Datos demo']]
const tab = ref('vehiculos')
const rows = ref([])
const busy = ref(false)

const vehicle = reactive({ placa: '', marca: '', modelo: '', color: '', tipo: 'LIVIANO', propietario: '', transportista: '' })
const auth_ = reactive({ placa: '', lista: 'BLANCA', motivo: '', vigente_hasta: '' })
const gate = reactive({ nombre: '', ubicacion: '' })
const user = reactive({ usuario: '', nombre: '', rol: 'OPERADOR', password: '' })
const demoN = ref(120)

const columns = computed(() => (rows.value[0] ? Object.keys(rows.value[0]) : []))

async function load() {
  if (tab.value === 'demo') { rows.value = []; return }
  try {
    rows.value = await api(`/api/admin/${tab.value}`)
  } catch (e) {
    session.notify(e.message, 'bad')
  }
}
async function run(fn) {
  busy.value = true
  try {
    const out = await fn()
    session.notify(out?.mensaje || (out?.creadas !== undefined ? `${out.creadas} operaciones de demostración creadas.` : `${out?.borradas ?? 0} operaciones de demostración borradas.`))
    await load()
    if (tab.value === 'garitas') await session.loadSystem(true)
    return true
  } catch (e) {
    session.notify(e.message, 'bad')
    return false
  } finally {
    busy.value = false
  }
}
const saveVehicle = () => run(() => api('/api/admin/vehiculos', { method: 'POST', body: vehicle }))
const saveAuth = () => run(() => api('/api/admin/autorizaciones', { method: 'POST', body: { ...auth_, vigente_hasta: auth_.vigente_hasta || null } }))
const revoke = () => run(() => api(`/api/admin/autorizaciones/${encodeURIComponent(auth_.placa)}`, { method: 'DELETE' }))
const saveGate = () => run(() => api('/api/admin/garitas', { method: 'POST', body: gate }))
const saveUser = async () => { if (await run(() => api('/api/admin/usuarios', { method: 'POST', body: user }))) user.password = '' }
const demo = () => run(() => api('/api/admin/demo', { method: 'POST', params: { n: demoN.value } }))
const clearDemo = () => run(() => api('/api/admin/demo', { method: 'DELETE' }))

const fmt = (v) => (v === true ? 'Sí' : v === false ? 'No' : v ?? '—')
watch(tab, load)
onMounted(load)
</script>

<template>
  <div class="mb-4 flex flex-wrap gap-1 rounded-xl bg-surface p-1 shadow-sm">
    <button v-for="[k, l] in TABS" :key="k" class="rounded-lg px-4 py-2 text-sm font-semibold transition"
            :class="tab === k ? 'bg-brand-600 text-white' : 'text-muted hover:bg-subtle-2'" @click="tab = k">{{ l }}</button>
  </div>
  <p v-if="!isAdmin" class="mb-4 rounded-xl bg-warn-soft px-4 py-3 text-sm font-semibold text-warn">
    Modo de consulta: solo el rol Administrador puede modificar datos.
  </p>

  <div class="grid gap-5" :class="isAdmin && tab !== 'propietarios' ? 'xl:grid-cols-3' : ''">
    <section v-if="isAdmin && tab !== 'propietarios'" class="card">
      <template v-if="tab === 'vehiculos'">
        <h2 class="card-title"><span class="icon-chip"><AppIcon name="car" /></span> Crear o actualizar vehículo</h2>
        <form class="space-y-3" @submit.prevent="saveVehicle">
          <input v-model.trim="vehicle.placa" class="field font-mono uppercase" placeholder="Placa (PBA-8901)" required />
          <div class="grid grid-cols-2 gap-3">
            <input v-model.trim="vehicle.marca" class="field" placeholder="Marca" />
            <input v-model.trim="vehicle.modelo" class="field" placeholder="Modelo" />
            <input v-model.trim="vehicle.color" class="field" placeholder="Color" />
            <select v-model="vehicle.tipo" class="field"><option>LIVIANO</option><option>CAMION</option><option>MOTO</option><option>OTRO</option></select>
          </div>
          <input v-model.trim="vehicle.propietario" class="field" placeholder="Propietario" />
          <input v-model.trim="vehicle.transportista" class="field" placeholder="Transportista (opcional)" />
          <button class="btn-primary w-full" :disabled="busy">Guardar vehículo</button>
        </form>
      </template>
      <template v-else-if="tab === 'autorizaciones'">
        <h2 class="card-title"><span class="icon-chip"><AppIcon name="lock" /></span> Lista blanca o restringida</h2>
        <form class="space-y-3" @submit.prevent="saveAuth">
          <input v-model.trim="auth_.placa" class="field font-mono uppercase" placeholder="Placa registrada" required />
          <select v-model="auth_.lista" class="field"><option value="BLANCA">Lista blanca (autorizado)</option><option value="RESTRINGIDA">Lista restringida (denegado)</option></select>
          <input v-model.trim="auth_.motivo" class="field" placeholder="Motivo" />
          <div><label class="field-label">Vigente hasta (opcional)</label><input v-model="auth_.vigente_hasta" type="date" class="field" /></div>
          <div class="flex gap-2">
            <button class="btn-primary flex-1" :disabled="busy">Asignar</button>
            <button type="button" class="btn-ghost" :disabled="busy || !auth_.placa" @click="revoke">Quitar de listas</button>
          </div>
        </form>
      </template>
      <template v-else-if="tab === 'garitas'">
        <h2 class="card-title"><span class="icon-chip"><AppIcon name="pin" /></span> Nueva garita</h2>
        <form class="space-y-3" @submit.prevent="saveGate">
          <input v-model.trim="gate.nombre" class="field" placeholder="Nombre (Garita 4)" required />
          <input v-model.trim="gate.ubicacion" class="field" placeholder="Ubicación" />
          <button class="btn-primary w-full" :disabled="busy">Agregar garita</button>
        </form>
      </template>
      <template v-else-if="tab === 'usuarios'">
        <h2 class="card-title"><span class="icon-chip"><AppIcon name="user" /></span> Nuevo usuario</h2>
        <form class="space-y-3" @submit.prevent="saveUser">
          <input v-model.trim="user.usuario" class="field" placeholder="Usuario" required minlength="3" />
          <input v-model.trim="user.nombre" class="field" placeholder="Nombre completo" required />
          <select v-model="user.rol" class="field"><option>OPERADOR</option><option>SUPERVISOR</option><option>ADMINISTRADOR</option></select>
          <input v-model="user.password" type="password" class="field" placeholder="Contraseña (mín. 8)" required minlength="8" autocomplete="new-password" />
          <button class="btn-primary w-full" :disabled="busy">Crear usuario</button>
        </form>
      </template>
      <template v-else-if="tab === 'demo'">
        <h2 class="card-title"><span class="icon-chip"><AppIcon name="chart" /></span> Datos de demostración</h2>
        <p class="mb-3 text-sm text-muted">Operaciones ficticias (origen DEMO) para mostrar el Dashboard. No son resultados del modelo y se pueden ocultar o borrar.</p>
        <div class="flex gap-2">
          <input v-model.number="demoN" type="number" min="1" max="1000" class="field !w-28" />
          <button class="btn-primary flex-1" :disabled="busy" @click="demo">Generar</button>
        </div>
        <button class="btn-red mt-3 w-full" :disabled="busy" @click="clearDemo">Borrar operaciones DEMO</button>
      </template>
    </section>

    <section v-if="tab !== 'demo'" class="card" :class="isAdmin && tab !== 'propietarios' ? 'xl:col-span-2' : ''">
      <p class="mb-3 font-semibold">{{ rows.length }} registros</p>
      <div class="table-wrap max-h-[65vh]">
        <table class="tbl">
          <thead><tr><th v-for="c in columns" :key="c">{{ c }}</th></tr></thead>
          <tbody><tr v-for="(r, i) in rows" :key="i"><td v-for="c in columns" :key="c">{{ fmt(r[c]) }}</td></tr></tbody>
        </table>
      </div>
    </section>
  </div>
</template>
