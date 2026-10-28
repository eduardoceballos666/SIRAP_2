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
const selectedTruckPlates = ref([])
const selectedUsers = ref([])
const selectedGateNames = ref([])

const vehicle = reactive({ placa: '', marca: '', modelo: '', color: '', tipo: '', propietario: '', transportista: '' })
const editingVehiclePlate = ref('')
const auth_ = reactive({ placa: '', lista: '', motivo: '', vigente_hasta: '' })
const gate = reactive({ nombre: '', ubicacion: '' })
const user = reactive({ usuario: '', nombre: '', rol: 'OPERADOR', password: '' })
const editingUser = ref('')
const demoN = ref(20)

const columns = computed(() => (rows.value[0] ? Object.keys(rows.value[0]) : []))
const selectableTrucks = computed(() => rows.value.filter((row) => row.tipo === 'CAMION' && row.placa).map((row) => row.placa))
const allTrucksSelected = computed(() => selectableTrucks.value.length > 0 && selectableTrucks.value.every((plate) => selectedTruckPlates.value.includes(plate)))
const selectableGates = computed(() => rows.value.filter((row) => row.nombre).map((row) => row.nombre))
const allGatesSelected = computed(() => selectableGates.value.length > 0 && selectableGates.value.every((name) => selectedGateNames.value.includes(name)))
const selectableUsers = computed(() => rows.value.filter((row) => row.usuario && row.usuario !== auth.user?.usuario).map((row) => row.usuario))
const allUsersSelected = computed(() => selectableUsers.value.length > 0 && selectableUsers.value.every((username) => selectedUsers.value.includes(username)))

async function load() {
  if (tab.value === 'demo') { rows.value = []; return }
  try {
    rows.value = await api(`/api/admin/${tab.value}`)
  } catch (e) {
    session.notify(e.message, 'bad')
  }
}
watch(tab, () => { selectedTruckPlates.value = []; selectedUsers.value = []; selectedGateNames.value = []; load() })
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
function resetVehicle() {
  Object.assign(vehicle, { placa: '', marca: '', modelo: '', color: '', tipo: '', propietario: '', transportista: '' })
  editingVehiclePlate.value = ''
}
function loadVehicleForEdit() {
  const key = plateKey(vehicle.placa)
  if (!key) {
    session.notify('Ingrese una placa para buscarla en la lista.', 'warn')
    return
  }
  if (editingVehiclePlate.value && plateKey(editingVehiclePlate.value) === key) {
    session.notify(`Los datos de ${editingVehiclePlate.value} ya están cargados.`, 'ok')
    return
  }
  const existing = rows.value.find((row) => plateKey(row.placa) === key)
  if (!existing) {
    if (editingVehiclePlate.value) {
      Object.assign(vehicle, { marca: '', modelo: '', color: '', tipo: '', propietario: '', transportista: '' })
      editingVehiclePlate.value = ''
    }
    session.notify('La placa no está registrada. Puede completar los campos para agregar el vehículo.', 'warn')
    return
  }
  Object.assign(vehicle, {
    placa: existing.placa,
    marca: existing.marca || '',
    modelo: existing.modelo || '',
    color: existing.color || '',
    tipo: existing.tipo || '',
    propietario: existing.propietario || '',
    transportista: existing.transportista || '',
  })
  editingVehiclePlate.value = existing.placa
  session.notify(`Datos de ${existing.placa} cargados para actualizar.`, 'ok')
}
async function saveVehicle() {
  const complete = vehicle.placa.trim() && vehicle.marca.trim() && vehicle.modelo.trim() &&
    vehicle.color.trim() && vehicle.tipo && vehicle.propietario.trim() && vehicle.transportista.trim()
  if (!complete) {
    session.notify('Complete todos los campos obligatorios antes de guardar el vehículo.', 'warn')
    return
  }
  const existing = rows.value.find((row) => plateKey(row.placa) === plateKey(vehicle.placa))
  if (existing && !window.confirm(`La placa ${existing.placa} ya existe en el listado. ¿Desea actualizarla?`)) {
    session.notify('No se actualizó el registro.', 'warn')
    return
  }
  if (await run(() => api('/api/admin/vehiculos', { method: 'POST', body: vehicle }))) resetVehicle()
}
function resetAuth() {
  Object.assign(auth_, { placa: '', lista: '', motivo: '', vigente_hasta: '' })
}
function loadAuthForEdit() {
  const key = plateKey(auth_.placa)
  if (!key) {
    session.notify('Ingrese una placa para buscarla en la lista.', 'warn')
    return
  }
  const existing = rows.value.find((row) => plateKey(row.placa) === key)
  if (!existing) {
    session.notify('La placa no está registrada en las listas.', 'warn')
    return
  }
  Object.assign(auth_, {
    placa: existing.placa || '',
    lista: existing.lista || '',
    motivo: existing.motivo || '',
    vigente_hasta: String(existing.vigente_hasta || '').slice(0, 10),
  })
  session.notify(`Datos de ${existing.placa} cargados.`, 'ok')
}
function plateKey(value) {
  return String(value || '').toUpperCase().replace(/[^A-Z0-9]/g, '')
}
async function saveAuth() {
  const complete = auth_.placa.trim() && auth_.lista && auth_.motivo.trim() && auth_.vigente_hasta
  if (!complete) {
    session.notify('Complete todos los campos obligatorios antes de asignar.', 'warn')
    return
  }
  const key = plateKey(auth_.placa)
  const existing = rows.value.find((row) => plateKey(row.placa) === key)
  let method = 'POST'
  let url = '/api/admin/autorizaciones'
  if (existing) {
    if (!window.confirm('La placa existe, ¿desea actualizar?')) {
      session.notify('No se actualizó la placa.', 'warn')
      resetAuth()
      return
    }
    method = 'PUT'
    url = `/api/admin/autorizaciones/${encodeURIComponent(existing.placa)}`
  }
  const saved = await run(() => api(url, { method, body: { ...auth_ } }))
  if (saved) resetAuth()
}
async function revoke() {
  if (!auth_.placa.trim()) {
    session.notify('Ingrese la placa que desea quitar de la lista.', 'warn')
    return
  }
  const saved = await run(() => api(`/api/admin/autorizaciones/${encodeURIComponent(auth_.placa)}`, { method: 'DELETE' }))
  if (saved) resetAuth()
}
function toggleTruckSelection(plate, checked) {
  selectedTruckPlates.value = checked
    ? [...new Set([...selectedTruckPlates.value, plate])]
    : selectedTruckPlates.value.filter((selected) => selected !== plate)
}
function selectAllTrucks(checked) {
  selectedTruckPlates.value = checked ? [...selectableTrucks.value] : []
}
function toggleGateSelection(name, checked) {
  selectedGateNames.value = checked
    ? [...new Set([...selectedGateNames.value, name])]
    : selectedGateNames.value.filter((selected) => selected !== name)
}
function selectAllGates(checked) {
  selectedGateNames.value = checked ? [...selectableGates.value] : []
}
async function updateSelectedGateState(activa) {
  if (!selectedGateNames.value.length || busy.value) return
  const nombres = [...selectedGateNames.value]
  const saved = await run(() => api('/api/admin/garitas/estado', {
    method: 'POST',
    body: { nombres, activa },
  }))
  if (saved) selectedGateNames.value = []
}
async function updateSelectedTruckAuthorization(lista) {
  if (!selectedTruckPlates.value.length || busy.value) return
  busy.value = true
  try {
    const out = await api('/api/admin/autorizaciones/seleccionadas', {
      method: 'POST', body: { placas: selectedTruckPlates.value, lista },
    })
    selectedTruckPlates.value = []
    session.notify(out.mensaje, 'ok')
    await load()
  } catch (e) {
    session.notify(e.message, 'bad')
  } finally {
    busy.value = false
  }
}
function resetGate() {
  Object.assign(gate, { nombre: '', ubicacion: '' })
}
async function saveGate() {
  const payload = { nombre: gate.nombre.trim(), ubicacion: gate.ubicacion.trim() }
  if (!payload.nombre || !payload.ubicacion) {
    session.notify('Complete el nombre y la ubicación antes de agregar la garita.', 'warn')
    return
  }
  if (await run(() => api('/api/admin/garitas', { method: 'POST', body: payload }))) resetGate()
}
function resetUser() {
  Object.assign(user, { usuario: '', nombre: '', rol: '', password: '' })
  editingUser.value = ''
}
function editUser(row) {
  editingUser.value = row.usuario
  Object.assign(user, { usuario: row.usuario, nombre: row.nombre || '', rol: row.rol || '', password: '' })
  session.notify(`Editando el usuario ${row.usuario}. Puede actualizar el nombre y el rol o restablecer su contraseña.`, 'ok')
}
async function saveUser() {
  if (editingUser.value) {
    const payload = { nombre: user.nombre.trim(), rol: user.rol }
    if (!payload.nombre || !payload.rol) {
      session.notify('Complete el nombre completo y el rol antes de guardar.', 'warn')
      return
    }
    const saved = await run(() => api(`/api/admin/usuarios/${encodeURIComponent(editingUser.value)}`, { method: 'PUT', body: payload }))
    if (saved) resetUser()
    return
  }
  const payload = {
    usuario: user.usuario.trim(),
    nombre: user.nombre.trim(),
    rol: user.rol,
    password: user.password,
  }
  if (!payload.usuario || payload.usuario.length < 3 || !/^[a-zA-Z0-9_.-]+$/.test(payload.usuario) ||
      !payload.nombre || !payload.rol || !payload.password.trim() || payload.password.length < 8) {
    session.notify('Complete todos los campos obligatorios. El usuario requiere 3 caracteres y la contraseña al menos 8.', 'warn')
    return
  }
  if (await run(() => api('/api/admin/usuarios', { method: 'POST', body: payload }))) resetUser()
}
async function resetUserPassword() {
  const username = editingUser.value
  const password = user.password
  if (!username) {
    session.notify('Seleccione un usuario de la tabla para restablecer su contraseña.', 'warn')
    return
  }
  if (password.length < 8) {
    session.notify('La nueva contraseña debe tener al menos 8 caracteres.', 'warn')
    return
  }
  if (!window.confirm(`¿Restablecer la contraseña de ${username}?`)) return
  const saved = await run(() => api(`/api/admin/usuarios/${encodeURIComponent(username)}/password`, {
    method: 'PUT',
    body: { password },
  }))
  if (saved) user.password = ''
}
function toggleUserSelection(username, checked) {
  selectedUsers.value = checked
    ? [...new Set([...selectedUsers.value, username])]
    : selectedUsers.value.filter((selected) => selected !== username)
}
function selectAllUsers(checked) {
  selectedUsers.value = checked ? [...selectableUsers.value] : []
}
async function updateSelectedUserState(activo) {
  if (!selectedUsers.value.length || busy.value) return
  const usuarios = [...selectedUsers.value]
  const saved = await run(() => api('/api/admin/usuarios/estado', {
    method: 'POST',
    body: { usuarios, activo },
  }))
  if (saved) selectedUsers.value = []
}
const demoMessage = ref('')
const demoMessageKind = ref('ok')
async function runDemo(action) {
  if (busy.value) return
  if (action === 'generate' && (!Number.isInteger(demoN.value) || demoN.value < 1 || demoN.value > 20)) {
    demoMessageKind.value = 'bad'
    demoMessage.value = 'Ingrese un número entero entre 1 y 20. No se permiten valores menores que 1 ni mayores que 20.'
    session.notify(demoMessage.value, 'bad')
    return
  }
  demoMessageKind.value = 'ok'
  demoMessage.value = action === 'generate' ? 'Generando operaciones de demostración…' : 'Borrando operaciones de demostración…'
  busy.value = true
  try {
    const out = action === 'generate'
      ? await api('/api/admin/demo', { method: 'POST', params: { n: demoN.value } })
      : await api('/api/admin/demo', { method: 'DELETE' })
    const count = action === 'generate' ? (out?.creadas ?? 0) : (out?.borradas ?? 0)
    demoMessage.value = action === 'generate'
      ? `Proceso terminado: se generaron ${count} operación(es) de demostración.`
      : `Proceso terminado: se borraron ${count} operación(es) DEMO.`
    session.notify(demoMessage.value, 'ok')
  } catch (e) {
    demoMessageKind.value = 'bad'
    demoMessage.value = `No se pudo completar la operación: ${e.message}`
    session.notify(demoMessage.value, 'bad')
  } finally {
    busy.value = false
  }
}

const fmt = (v) => (v === true ? 'Sí' : v === false ? 'No' : v ?? '—')
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
        <form class="space-y-3" novalidate @submit.prevent="saveVehicle">
          <input v-model.trim="vehicle.placa" class="field font-mono uppercase" placeholder="Placa (PBA-8901) *" required @keydown.enter.prevent="loadVehicleForEdit" />
          <div class="grid grid-cols-2 gap-3">
            <input v-model.trim="vehicle.marca" class="field bg-subtle font-semibold" placeholder="Marca *" required />
            <input v-model.trim="vehicle.modelo" class="field bg-subtle font-semibold" placeholder="Modelo *" required />
            <input v-model.trim="vehicle.color" class="field bg-subtle font-semibold" placeholder="Color *" required />
            <select v-model="vehicle.tipo" class="field" required><option disabled value="">Seleccione tipo *</option><option value="LIVIANO">LIVIANO</option><option value="CAMION">CAMION</option><option value="MOTO">MOTO</option><option value="OTRO">OTRO</option></select>
          </div>
          <input v-model.trim="vehicle.propietario" class="field bg-subtle font-semibold" placeholder="Propietario *" required />
          <input v-model.trim="vehicle.transportista" class="field bg-subtle font-semibold" placeholder="Transportista *" required />
          <div class="flex gap-2">
            <button class="btn-primary flex-1" :disabled="busy">Guardar vehículo</button>
            <button type="button" class="btn-ghost flex-1" :disabled="busy" @click="resetVehicle">Limpiar campos</button>
          </div>
        </form>
      </template>
      <template v-else-if="tab === 'autorizaciones'">
        <h2 class="card-title"><span class="icon-chip"><AppIcon name="lock" /></span> Lista blanca o restringida</h2>
        <form class="space-y-3" @submit.prevent="saveAuth">
          <input v-model.trim="auth_.placa" class="field font-mono uppercase" placeholder="Placa registrada *" required @keydown.enter.prevent="loadAuthForEdit" />
          <select v-model="auth_.lista" class="field" required><option disabled value="">Seleccione una lista *…</option><option value="BLANCA">Lista blanca (autorizado)</option><option value="RESTRINGIDA">Lista restringida (denegado)</option></select>
          <input v-model.trim="auth_.motivo" class="field" placeholder="Motivo *" required />
          <div><label class="field-label" for="authorization-expiry">Vigente hasta *</label><input id="authorization-expiry" v-model="auth_.vigente_hasta" type="date" class="field" required /></div>
          <div class="flex gap-2">
            <button class="btn-primary flex-1" :disabled="busy">Asignar</button>
            <button type="button" class="btn-ghost flex-1" :disabled="busy" @click="resetAuth">Limpiar Campos</button>
            <button type="button" class="btn-ghost flex-1" :disabled="busy || !auth_.placa" @click="revoke">Quitar de listas</button>
          </div>
        </form>
      </template>
      <template v-else-if="tab === 'garitas'">
        <h2 class="card-title"><span class="icon-chip"><AppIcon name="pin" /></span> Nueva garita</h2>
        <form class="space-y-3" @submit.prevent="saveGate">
          <input v-model.trim="gate.nombre" class="field" placeholder="Nombre (Garita 4) *" required maxlength="60" />
          <input v-model.trim="gate.ubicacion" class="field" placeholder="Ubicación *" required maxlength="120" />
          <div class="flex gap-2">
            <button class="btn-primary flex-1" :disabled="busy">Agregar garita</button>
            <button type="button" class="btn-ghost flex-1" :disabled="busy" @click="resetGate">Limpiar Campos</button>
          </div>
        </form>
      </template>
      <template v-else-if="tab === 'usuarios'">
        <h2 class="card-title"><span class="icon-chip"><AppIcon name="user" /></span> {{ editingUser ? 'Editar usuario' : 'Nuevo usuario' }}</h2>
        <form class="space-y-3" @submit.prevent="saveUser">
          <input v-model.trim="user.usuario" class="field" placeholder="Usuario *" required minlength="3" maxlength="40" pattern="[a-zA-Z0-9_.-]+" autocomplete="username" :disabled="busy || Boolean(editingUser)" />
          <input v-model.trim="user.nombre" class="field" placeholder="Nombre completo *" required maxlength="120" autocomplete="name" />
          <select v-model="user.rol" class="field" required>
            <option disabled value="">Seleccione un rol *</option>
            <option value="OPERADOR">OPERADOR</option>
            <option value="SUPERVISOR">SUPERVISOR</option>
            <option value="ADMINISTRADOR">ADMINISTRADOR</option>
          </select>
          <template v-if="!editingUser">
            <input v-model="user.password" type="password" class="field" placeholder="Contraseña * (mín. 8)" required minlength="8" maxlength="128" autocomplete="new-password" />
            <button class="btn-primary w-full" :disabled="busy">Crear usuario</button>
          </template>
          <template v-else>
            <div class="rounded-xl border border-line bg-subtle p-3">
              <label class="field-label" :for="'reset-user-password'">Nueva contraseña de {{ editingUser }}</label>
              <input id="reset-user-password" v-model="user.password" type="password" class="field" placeholder="Nueva contraseña (mín. 8)" minlength="8" maxlength="128" autocomplete="new-password" />
              <button type="button" class="btn-yellow mt-2 w-full" :disabled="busy || user.password.length < 8" @click="resetUserPassword">Restablecer contraseña</button>
            </div>
            <button class="btn-primary w-full" :disabled="busy">Guardar cambios</button>
          </template>
          <button type="button" class="btn-ghost w-full" :disabled="busy" @click="resetUser">Limpiar Campos</button>
        </form>
      </template>
      <template v-else-if="tab === 'demo'">
        <h2 class="card-title"><span class="icon-chip"><AppIcon name="chart" /></span> Datos de demostración</h2>
        <p class="mb-3 text-sm text-muted">Operaciones ficticias (origen DEMO) para mostrar el Dashboard. No son resultados del modelo y se pueden ocultar o borrar.</p>
        <div class="flex gap-2">
          <input v-model.number="demoN" type="number" min="1" max="20" step="1" inputmode="numeric" class="field !w-28" aria-label="Cantidad de operaciones demo, de 1 a 20" />
          <button class="btn-primary flex-1" :disabled="busy" @click="runDemo('generate')">Generar</button>
        </div>
        <button class="btn-red mt-3 w-full" :disabled="busy" @click="runDemo('clear')">Borrar operaciones DEMO</button>
        <p v-if="demoMessage" class="mt-3 rounded-lg bg-subtle px-3 py-2 text-sm font-semibold text-muted"
           :class="demoMessageKind === 'bad' ? 'text-warn' : ''" role="status" aria-live="polite">
          {{ demoMessage }}
        </p>
      </template>
    </section>

    <section v-if="tab !== 'demo'" class="card" :class="isAdmin && tab !== 'propietarios' ? 'xl:col-span-2' : ''">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
        <p class="font-semibold">{{ rows.length }} registros</p>
        <div v-if="isAdmin && tab === 'vehiculos'" class="flex flex-wrap items-center gap-2">
          <span class="text-xs text-muted">{{ selectedTruckPlates.length }} camión(es) seleccionados</span>
          <button class="btn-primary" :disabled="busy || !selectedTruckPlates.length" @click="updateSelectedTruckAuthorization('BLANCA')">Autorizar seleccionados</button>
          <button class="btn-ghost" :disabled="busy || !selectedTruckPlates.length" @click="updateSelectedTruckAuthorization(null)">Dejar sin autorización</button>
        </div>
        <div v-if="isAdmin && tab === 'usuarios'" class="flex flex-wrap items-center gap-2">
          <span class="text-xs text-muted">{{ selectedUsers.length }} usuario(s) seleccionados</span>
          <button class="btn-red" :disabled="busy || !selectedUsers.length" @click="updateSelectedUserState(false)">Inactivar usuario</button>
          <button class="btn-primary" :disabled="busy || !selectedUsers.length" @click="updateSelectedUserState(true)">Activar usuario</button>
        </div>
        <div v-if="isAdmin && tab === 'garitas'" class="flex flex-wrap items-center gap-2">
          <span class="text-xs text-muted">{{ selectedGateNames.length }} garita(s) seleccionadas</span>
          <button class="btn-red" :disabled="busy || !selectedGateNames.length" @click="updateSelectedGateState(false)">Inactivar garita</button>
          <button class="btn-primary" :disabled="busy || !selectedGateNames.length" @click="updateSelectedGateState(true)">Activar garita</button>
        </div>
      </div>
      <div class="table-wrap max-h-[65vh]">
        <table class="tbl">
          <thead><tr>
            <th v-if="isAdmin && tab === 'usuarios'"><input type="checkbox" aria-label="Seleccionar todos los usuarios" :checked="allUsersSelected" :disabled="!selectableUsers.length" @change="selectAllUsers($event.target.checked)" /></th>
            <th v-if="isAdmin && tab === 'garitas'"><input type="checkbox" aria-label="Seleccionar todas las garitas" :checked="allGatesSelected" :disabled="!selectableGates.length" @change="selectAllGates($event.target.checked)" /></th>
            <th v-if="isAdmin && tab === 'vehiculos'"><input type="checkbox" aria-label="Seleccionar todos los camiones" :checked="allTrucksSelected" :disabled="!selectableTrucks.length" @change="selectAllTrucks($event.target.checked)" /></th>
            <th v-for="c in columns" :key="c">{{ c }}</th>
            <th v-if="isAdmin && tab === 'usuarios'">Acciones</th>
          </tr></thead>
          <tbody><tr v-for="(r, i) in rows" :key="i">
            <td v-if="isAdmin && tab === 'usuarios'"><input type="checkbox" :aria-label="'Seleccionar usuario ' + r.usuario" :checked="selectedUsers.includes(r.usuario)" :disabled="r.usuario === auth.user?.usuario" @change="toggleUserSelection(r.usuario, $event.target.checked)" /></td>
            <td v-if="isAdmin && tab === 'garitas'"><input type="checkbox" :aria-label="'Seleccionar garita ' + r.nombre" :checked="selectedGateNames.includes(r.nombre)" @change="toggleGateSelection(r.nombre, $event.target.checked)" /></td>
            <td v-if="isAdmin && tab === 'vehiculos'"><input v-if="r.tipo === 'CAMION'" type="checkbox" :aria-label="`Seleccionar camión ${r.placa}`" :checked="selectedTruckPlates.includes(r.placa)" @change="toggleTruckSelection(r.placa, $event.target.checked)" /></td>
            <td v-for="c in columns" :key="c">{{ fmt(r[c]) }}</td>
            <td v-if="isAdmin && tab === 'usuarios'">
              <button class="btn-ghost whitespace-nowrap" :disabled="busy" @click="editUser(r)">Editar</button>
            </td>
          </tr></tbody>
        </table>
      </div>
    </section>
  </div>
</template>
