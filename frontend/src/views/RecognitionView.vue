<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import ImageViewer from '@/components/ImageViewer.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import ResultCard from '@/components/ResultCard.vue'
import { api } from '@/lib/api'
import { ACTION, RESULT, TONE_PILL, pct } from '@/lib/format'
import { useSessionStore } from '@/stores/session'
import { useAuthStore } from '@/stores/auth'

const session = useSessionStore()
const auth = useAuthStore()
const now = ref(new Date())
const displayClock = computed(() => now.value.toLocaleString('es-EC', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }))
const cameraPanel = ref(null)
const fullscreen = ref(false)
let clockTimer

const source = ref('ejemplos')
const samples = ref([])
const selectedSample = ref('')
const sourceLabel = ref('') // de dónde vino la imagen (para la tabla de lecturas)
const lecturaId = ref(null)
const file = ref(null) // Blob a reconocer
const preview = ref('')
const stamp = ref('')

const loading = ref(false)
const recognition = ref(null)
const decision = ref(null)
const manualPlate = ref('') // placa corregida o escrita por el operador
const origin = ref('DETECCION')
const busy = ref(false)
const done = ref(false) // ya se registró esta lectura

const manualOpen = ref(false)
const helpOpen = ref(false)
const detailsOpen = ref(false)
const readingsOpen = ref(false)
const registrationOpen = ref(false)
const registrationPromptDismissed = ref(false)
const vehicleDraft = reactive({ marca: '', modelo: '', color: '', propietario: '', transportista: '' })
const showCapture = ref(false)
const motivo = ref('')

// --- cámara -----------------------------------------------------------------------------
const video = ref(null)
let stream = null
const cameraError = ref('')

async function toggleFullscreen() {
  try {
    if (document.fullscreenElement === cameraPanel.value) await document.exitFullscreen()
    else await cameraPanel.value?.requestFullscreen()
  } catch {
    session.notify('No se pudo abrir la cámara en pantalla completa.', 'warn')
  }
}
function syncFullscreen() { fullscreen.value = document.fullscreenElement === cameraPanel.value }

async function startCamera() {
  cameraError.value = ''
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment', width: { ideal: 1280 } } })
    video.value.srcObject = stream
  } catch {
    cameraError.value = 'No se pudo acceder a la cámara (permiso denegado o no disponible).'
  }
}
function stopCamera() {
  stream?.getTracks().forEach((t) => t.stop())
  stream = null
}
function capture() {
  const v = video.value
  if (!v?.videoWidth) return
  const canvas = document.createElement('canvas')
  canvas.width = v.videoWidth
  canvas.height = v.videoHeight
  canvas.getContext('2d').drawImage(v, 0, 0)
  canvas.toBlob((blob) => { setImage(blob, 'Cámara'); showCapture.value = true; recognize() }, 'image/jpeg', 0.92)
}
function setSource(name) {
  source.value = name
  showCapture.value = false
  if (name === 'camara') setTimeout(startCamera, 0)
  else stopCamera()
}
onBeforeUnmount(() => {
  stopCamera()
  clearInterval(clockTimer)
  document.removeEventListener('fullscreenchange', syncFullscreen)
})

// --- imagen -----------------------------------------------------------------------------
function reset() {
  recognition.value = null
  decision.value = null
  manualPlate.value = ''
  origin.value = 'DETECCION'
  done.value = false
  registrationPromptDismissed.value = false
}
function setImage(blob, label = '') {
  sourceLabel.value = label
  if (preview.value) URL.revokeObjectURL(preview.value)
  file.value = blob
  preview.value = URL.createObjectURL(blob)
  stamp.value = new Date().toLocaleString('es-EC')
  reset()
}
function clearCurrentReading() {
  if (loading.value || busy.value) return
  if (preview.value) URL.revokeObjectURL(preview.value)
  file.value = null
  preview.value = ''
  stamp.value = ''
  sourceLabel.value = ''
  selectedSample.value = ''
  showCapture.value = false
  reset()
  Object.assign(vehicleDraft, { marca: '', modelo: '', color: '', propietario: '', transportista: '' })
  registrationOpen.value = false
  manualOpen.value = false
  detailsOpen.value = false
  motivo.value = ''
}
async function pickSample(name) {
  selectedSample.value = name
  const res = await api(`/api/samples/${name}`, { raw: true })
  setImage(await res.blob(), samples.value.find((s) => s.nombre === name)?.etiqueta.split(' (')[0] || name)
  await recognize()
}
async function onUpload(event) {
  const f = event.target.files?.[0]
  if (!f) return
  setImage(f, f.name)
  await recognize()
  event.target.value = ''
}

async function recognize() {
  if (!file.value) {
    session.notify('Primero elija o capture una imagen.', 'warn')
    return
  }
  loading.value = true
  reset()
  try {
    const form = new FormData()
    form.append('file', file.value, 'imagen.jpg')
    const data = await api('/api/recognize', { method: 'POST', form })
    recognition.value = data.recognition
    decision.value = data.decision
    manualPlate.value = data.recognition.plate || ''
    session.addLectura({
      fuente: sourceLabel.value || 'Imagen', placa: data.recognition.plate, resultado: data.decision.resultado,
      confianza: data.recognition.ocr_confidence, ms: data.recognition.timings_ms?.total, origen: 'DETECCION',
    })
    lecturaId.value = session.lecturas[0].id
  } catch (e) {
    session.notify(e.message, 'bad')
  } finally {
    loading.value = false
  }
}

async function verifyManual() {
  if (!manualPlate.value) return
  busy.value = true
  try {
    const data = await api('/api/plates/verify', { method: 'POST', body: { placa: manualPlate.value } })
    manualPlate.value = data.placa
    decision.value = data.decision
    origin.value = 'MANUAL'
    done.value = false
    registrationPromptDismissed.value = false
    session.addLectura({ fuente: 'Escrita a mano', placa: data.placa, resultado: data.decision.resultado,
      confianza: null, ms: null, origen: 'MANUAL' })
    lecturaId.value = session.lecturas[0].id
  } catch (e) {
    session.notify(e.message, 'bad')
  } finally {
    busy.value = false
  }
}

// --- acciones -----------------------------------------------------------------------------
const tone = computed(() => RESULT[decision.value?.resultado]?.tone)
const plateShown = computed(() => (origin.value === 'MANUAL' ? manualPlate.value : recognition.value?.plate) || '')
const canOpen = computed(() => decision.value?.permite_apertura && !done.value)
const vehicle = computed(() => decision.value?.vehiculo)
const decisionLabel = computed(() => decision.value?.resultado === 'NO_REGISTRADO' && vehicle.value
  ? 'SIN AUTORIZACIÓN'
  : RESULT[decision.value?.resultado]?.label || 'EN ESPERA')
const needsVehicleRegistration = computed(() => decision.value?.resultado === 'NO_REGISTRADO' && !vehicle.value && !!plateShown.value)

function startVehicleRegistration() {
  Object.assign(vehicleDraft, { marca: '', modelo: '', color: '', propietario: '', transportista: '' })
  registrationOpen.value = true
}

async function saveVehicle() {
  if (!plateShown.value) return
  busy.value = true
  try {
    const saved = await api('/api/plates/register', {
      method: 'POST',
      body: { placa: plateShown.value, ...vehicleDraft, tipo: 'CAMION' },
    })
    const checked = await api('/api/plates/verify', { method: 'POST', body: { placa: saved.placa } })
    manualPlate.value = checked.placa
    decision.value = checked.decision
    origin.value = 'MANUAL'
    registrationOpen.value = false
    registrationPromptDismissed.value = true
    session.notify(`${saved.mensaje} Puede continuar con la autorización automática.`, 'ok')
  } catch (e) {
    session.notify(e.message, 'bad')
  } finally {
    busy.value = false
  }
}

async function register(accion) {
  if (!decision.value) {
    session.notify('Procese una imagen o verifique una placa antes de registrar.', 'warn')
    return
  }
  busy.value = true
  try {
    const out = await api('/api/operations', {
      method: 'POST',
      body: {
        garita: session.garita,
        tipo_movimiento: session.movimiento,
        accion,
        placa_leida: recognition.value?.plate || recognition.value?.plate_raw || null,
        placa_final: plateShown.value || null,
        confianza_ocr: recognition.value?.ocr_confidence ?? null,
        det_confidence: recognition.value?.detector_is_model ? recognition.value.det_confidence : null,
        motivo: accion === 'APERTURA_MANUAL' ? motivo.value.trim() : null,
        origen: origin.value,
        tiempo_ms: recognition.value?.timings_ms?.total ?? null,
      },
    })
    done.value = true
    session.markRegistered(lecturaId.value, out.accion)
    manualOpen.value = false
    motivo.value = ''
    const sim = out.barrera_abierta && out.barrera_simulada ? ' (barrera simulada)' : ''
    session.notify(out.mensaje + sim, out.accion === 'RECHAZO' ? 'warn' : 'ok')
  } catch (e) {
    session.notify(e.message, 'bad')
  } finally {
    busy.value = false
  }
}

function exportLecturas() {
  const head = ['hora', 'fuente', 'placa', 'resultado', 'confianza_ocr', 'tiempo_ms', 'origen', 'registro']
  const rows = session.lecturas.map((l) => [l.hora, l.fuente, l.placa || '', l.resultado,
    l.confianza ?? '', l.ms ? Math.round(l.ms) : '', l.origen, l.registro || ''])
  const csv = [head, ...rows].map((r) => r.map((v) => `"${String(v).replaceAll('"', '""')}"`).join(',')).join('\n')
  const url = URL.createObjectURL(new Blob(['\ufeff' + csv], { type: 'text/csv' }))
  Object.assign(document.createElement('a'), { href: url, download: 'sirap_lecturas_sesion.csv' }).click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  document.addEventListener('fullscreenchange', syncFullscreen)
  clockTimer = setInterval(() => { now.value = new Date() }, 1000)
  try {
    await session.loadSystem()
    samples.value = await api('/api/samples')
  } catch (e) {
    session.notify(e.message, 'bad')
  }
})
</script>

<template>
  <div class="access-workspace">
    <div class="control-strip">
      <div class="control-field"><span>Punto de control</span><strong><AppIcon name="pin" :size="17" /> Garita de acceso</strong></div>
      <label class="control-field" for="garita"><span>Garita</span><select id="garita" v-model="session.garita" class="field"><option v-for="g in session.system?.garitas || []" :key="g">{{ g }}</option></select></label>
      <div class="control-field"><span>Operador</span><strong><AppIcon name="user" :size="17" /> {{ auth.user?.nombre || '—' }}</strong></div>
      <label class="control-field" for="mov"><span>Operación</span><select id="mov" v-model="session.movimiento" class="field"><option value="ENTRADA">Entrada</option><option value="SALIDA">Salida</option></select></label>
      <button class="btn-ghost help-button" aria-label="Ayuda" title="Ayuda" @click="helpOpen = true"><AppIcon name="help" :size="17" /><span>Ayuda</span></button>
      <div class="workspace-clock"><AppIcon name="calendar" :size="18" /> {{ displayClock }}</div>
    </div>

    <div class="access-grid">
      <section ref="cameraPanel" class="card camera-panel" aria-label="Cámara e imagen">
        <div class="panel-toolbar camera-toolbar">
          <h2><AppIcon name="camera" :size="18" /> Lectura del vehículo</h2>
          <div class="source-tabs" role="group" aria-label="Fuente de imagen">
            <button v-for="s in [['camara', 'En vivo'], ['ejemplos', 'Ejemplos'], ['subir', 'Subir imagen']]" :key="s[0]" :aria-pressed="source === s[0]" :class="{ active: source === s[0] }" @click="setSource(s[0])">{{ s[1] }}</button>
          </div>
          <button class="btn-ghost fullscreen-button" :aria-label="fullscreen ? 'Salir de pantalla completa' : 'Ver en pantalla completa'" :title="fullscreen ? 'Salir de pantalla completa' : 'Ver en pantalla completa'" @click="toggleFullscreen">
            <AppIcon :name="fullscreen ? 'minimize' : 'fullscreen'" :size="17" /><span>{{ fullscreen ? 'Salir' : 'Pantalla completa' }}</span>
          </button>
        </div>

        <select v-if="source === 'ejemplos'" :value="selectedSample" class="field sample-select" aria-label="Probar con un ejemplo" :disabled="loading" @change="pickSample($event.target.value)">
          <option disabled value="">Seleccionar imagen de ejemplo…</option><option v-for="s in samples" :key="s.nombre" :value="s.nombre">{{ s.etiqueta }}</option>
        </select>
        <label v-else-if="source === 'subir'" class="upload-compact"><AppIcon name="upload" :size="17" /><span>Elegir imagen · JPG, PNG o WEBP · máx. 10 MB</span><input type="file" accept="image/jpeg,image/png,image/webp" class="hidden" @change="onUpload" /></label>
        <div v-else class="live-camera-tools">
          <button class="btn-primary" :disabled="loading" @click="capture"><AppIcon name="camera" :size="16" /> Capturar y reconocer</button>
          <button v-if="preview" class="btn-ghost" @click="showCapture = !showCapture">{{ showCapture ? 'Ver cámara en vivo' : 'Ver captura' }}</button>
        </div>

        <p v-if="source === 'camara' && cameraError" role="alert" class="camera-error">{{ cameraError }}</p>
        <div class="camera-stage">
          <video v-if="source === 'camara'" v-show="!showCapture" ref="video" autoplay playsinline muted></video>
          <ImageViewer v-show="source !== 'camara' || showCapture" class="compact-viewer" :src="preview" :box="recognition?.box" :width="recognition?.image_width" :height="recognition?.image_height" :tone="tone" :label="recognition?.plate" :garita="session.garita" :stamp="stamp" :loading="loading" />
        </div>
        <div class="camera-meta">
          <span>{{ recognition ? recognition.detector + ' · ' + recognition.timings_ms.total?.toFixed(0) + ' ms' : 'Imagen de la garita · lista para procesar' }}</span>
          <div class="camera-meta-actions">
            <button class="btn-ghost clear-reading-button" :disabled="loading || busy || (!file && !decision && !manualPlate)" @click="clearCurrentReading"><AppIcon name="trash" :size="14" /> Limpiar lectura</button>
            <button class="btn-ghost" :disabled="loading || !file" @click="recognize"><AppIcon name="refresh" :size="15" /> Reprocesar</button>
          </div>
        </div>

        <section class="reading-gallery" aria-label="Lecturas recientes">
          <div class="reading-gallery-head"><strong>Lecturas recientes</strong><div><button class="text-link" @click="readingsOpen = true">Ver todas ({{ session.lecturas.length }})</button><RouterLink class="text-link" to="/historial">Historial</RouterLink></div></div>
          <div v-if="session.lecturas.length" class="reading-cards">
            <article v-for="l in session.lecturas.slice(0, 4)" :key="l.id" class="reading-card">
              <span class="reading-icon"><AppIcon name="car" :size="20" /></span>
              <span class="reading-copy"><strong>{{ l.placa || 'Sin placa' }}</strong><small>{{ l.hora }} · {{ RESULT[l.resultado]?.label || l.resultado }}</small></span>
            </article>
          </div>
          <p v-else class="reading-empty">Las lecturas de esta sesión aparecerán aquí.</p>
        </section>
      </section>

      <div class="decision-column" :class="tone ? 'tone-' + tone : 'tone-neutral'">
        <section class="card access-result-card" :class="tone ? 'tone-' + tone : 'tone-neutral'" role="status" aria-live="polite">
          <span class="result-mark"><AppIcon :name="tone === 'ok' ? 'check' : tone === 'bad' ? 'x' : tone === 'warn' ? 'alert' : 'bolt'" :size="28" :stroke="2.5" /></span>
          <div class="result-copy">
            <span class="eyebrow">Resultado de acceso</span>
            <strong>{{ loading ? 'PROCESANDO…' : decisionLabel }}</strong>
            <span class="result-detail">{{ decision?.detalle || 'Seleccione o capture una imagen para verificar' }}</span>
            <button v-if="decision?.resultado === 'DENEGADO'" class="result-action" :disabled="busy || done" @click="register('RECHAZO')">Registrar rechazo</button>
            <button v-else-if="decision && !decision.permite_apertura" class="result-action" :disabled="busy || done" @click="register('SOLO_REGISTRO')">Registrar sin abrir</button>
            <button v-if="decision" class="text-link result-detail-link" @click="detailsOpen = true">Ver detalle completo</button>
          </div>
          <div class="ocr-meter">
            <span><AppIcon name="chart" :size="15" /> Confianza OCR</span>
            <strong>{{ origin === 'MANUAL' ? 'Manual' : pct(recognition?.ocr_confidence) }}</strong>
            <div class="meter-track" role="progressbar" :aria-valuenow="Math.round((recognition?.ocr_confidence || 0) * 100)" aria-valuemin="0" aria-valuemax="100"><i :style="{ width: Math.max(0, Math.min(100, (recognition?.ocr_confidence || 0) * 100)) + '%' }"></i></div>
          </div>
        </section>

        <section class="card plate-panel" aria-label="Placa identificada">
          <div class="section-heading"><h2><AppIcon name="camera" :size="19" /> Placa identificada</h2><span>{{ origin === 'MANUAL' ? 'Manual' : 'OCR' }}</span></div>
          <div class="plate-line"><div class="compact-plate">{{ plateShown || '———-————' }}</div><img v-if="recognition?.crop_jpeg_base64" :src="'data:image/jpeg;base64,' + recognition.crop_jpeg_base64" alt="Recorte de la placa" /></div>
          <form class="plate-form" @submit.prevent="verifyManual"><input v-model.trim="manualPlate" class="field font-mono uppercase" aria-label="Corregir o escribir placa" placeholder="Corregir / escribir placa" maxlength="12" /><button class="btn-ghost" :disabled="busy || !manualPlate">Verificar</button></form>
        </section>

        <section class="card vehicle-panel" aria-label="Detalles del vehículo">
          <div class="section-heading"><h2><AppIcon name="car" :size="19" /> Detalles del vehículo</h2><button v-if="vehicle" class="text-link" @click="detailsOpen = true">Más datos</button></div>
          <div v-if="needsVehicleRegistration && !registrationPromptDismissed" class="registration-prompt" role="status">
            <div><strong>Esta placa no está registrada.</strong><span>¿Desea guardar el camión en la base de datos?</span></div>
            <div class="registration-prompt-actions"><button class="btn-primary" :disabled="busy" @click="startVehicleRegistration">Sí, registrar</button><button class="btn-ghost" @click="registrationPromptDismissed = true">No, continuar</button></div>
          </div>
          <dl class="vehicle-rows">
            <div><dt>Marca</dt><dd :title="vehicle?.marca || ''">{{ vehicle?.marca || '—' }}</dd></div>
            <div><dt>Modelo</dt><dd :title="vehicle?.modelo || ''">{{ vehicle?.modelo || '—' }}</dd></div>
            <div><dt>Color</dt><dd :title="vehicle?.color || ''">{{ vehicle?.color || '—' }}</dd></div>
            <div><dt>Propietario</dt><dd :title="vehicle?.propietario || ''">{{ vehicle?.propietario || '—' }}</dd></div>
            <div><dt>Transportista</dt><dd :title="vehicle?.transportista || ''">{{ vehicle?.transportista || '—' }}</dd></div>
          </dl>
          <p v-if="done" class="registered-note" role="status">✓ Lectura registrada en el historial.</p>
        </section>
      </div>
    </div>

    <div class="access-action-bar" aria-label="Acciones de acceso">
      <button class="btn-yellow action-button" :disabled="!canOpen || busy" @click="register('APERTURA_AUTOMATICA')"><AppIcon name="barrier" :size="20" /><span>Registrar y abrir barrera</span></button>
      <button class="btn-red action-button" :disabled="!file || loading" @click="recognize"><AppIcon name="settings" :size="20" /><span>Procesar detección automática</span></button>
      <button class="btn-navy action-button" :disabled="!decision || busy || done" @click="manualOpen = true"><AppIcon name="lock" :size="19" /><span>Apertura manual (Contingencia)</span></button>
    </div>
  </div>
  <ModalDialog :open="helpOpen" title="Cómo registrar un acceso" @close="helpOpen = false"><ol class="list-decimal space-y-3 pl-5"><li>Elija un ejemplo, suba una imagen o capture desde la cámara.</li><li>Revise la placa, el vehículo y el resultado. Corrija la placa y pulse Verificar si es necesario.</li><li>Autorice y abra solo cuando el resultado lo permita, o registre sin abrir. La apertura manual requiere un motivo.</li><li>Las lecturas solo se guardan en el historial al registrar una acción.</li></ol><button class="btn-primary mt-4" @click="helpOpen = false">Entendido</button></ModalDialog>
  <ModalDialog :open="registrationOpen" title="Registrar camión nuevo" @close="registrationOpen = false">
    <form class="vehicle-registration-form" @submit.prevent="saveVehicle">
      <div class="registration-plate"><span>Placa detectada</span><strong>{{ plateShown }}</strong></div>
      <label class="field-label" for="vehicle-make">Marca *</label><input id="vehicle-make" v-model.trim="vehicleDraft.marca" class="field" required maxlength="80" placeholder="Ej.: Chevrolet" />
      <label class="field-label" for="vehicle-model">Modelo *</label><input id="vehicle-model" v-model.trim="vehicleDraft.modelo" class="field" required maxlength="80" placeholder="Ej.: NLR Reward" />
      <label class="field-label" for="vehicle-color">Color *</label><input id="vehicle-color" v-model.trim="vehicleDraft.color" class="field" required maxlength="40" placeholder="Ej.: Blanco" />
      <label class="field-label" for="vehicle-owner">Propietario *</label><input id="vehicle-owner" v-model.trim="vehicleDraft.propietario" class="field" required maxlength="120" placeholder="Nombre del propietario" />
      <label class="field-label" for="vehicle-carrier">Transportista</label><input id="vehicle-carrier" v-model.trim="vehicleDraft.transportista" class="field" maxlength="120" placeholder="Empresa transportista (opcional)" />
      <p class="registration-note">Se guardará como camión y quedará autorizado en la lista blanca.</p>
      <div class="mt-4 flex justify-end gap-2"><button type="button" class="btn-ghost" @click="registrationOpen = false">Cancelar</button><button type="submit" class="btn-primary" :disabled="busy">{{ busy ? 'Guardando…' : 'Guardar camión' }}</button></div>
    </form>
  </ModalDialog>
  <ModalDialog :open="detailsOpen" title="Detalle de la verificación" @close="detailsOpen = false"><ResultCard :decision="decision" :loading="loading" /><dl v-if="vehicle" class="mt-3 space-y-2 text-sm"><div v-for="[k,v] in [['Marca', vehicle.marca], ['Modelo', vehicle.modelo], ['Color', vehicle.color], ['Propietario', vehicle.propietario], ['Transportista', vehicle.transportista]]" :key="k"><dt class="font-bold">{{ k }}</dt><dd class="break-words">{{ v || '—' }}</dd></div></dl><button class="btn-ghost mt-4" @click="detailsOpen = false">Cerrar</button></ModalDialog>
  <ModalDialog :open="readingsOpen" title="Lecturas de esta sesión" @close="readingsOpen = false"><div class="max-h-[60vh] overflow-auto">
    <div class="table-wrap">
      <table class="tbl">
        <thead><tr><th>Hora</th><th>Imagen</th><th>Placa</th><th>Resultado</th><th>Confianza OCR</th><th>Tiempo</th><th>Registro</th></tr></thead>
        <tbody>
          <tr v-for="l in session.lecturas" :key="l.id">
            <td>{{ l.hora }}</td><td class="max-w-56 truncate" :title="l.fuente">{{ l.fuente }}</td>
            <td class="font-bold">{{ l.placa || '—' }}</td>
            <td><span class="pill" :class="TONE_PILL[RESULT[l.resultado]?.tone]">{{ RESULT[l.resultado]?.label }}</span></td>
            <td>
              <div v-if="l.confianza !== null" class="flex items-center gap-2">
                <div class="h-2 w-20 overflow-hidden rounded-full bg-subtle-2">
                  <div class="h-full rounded-full" :class="l.confianza >= 0.99 ? 'bg-ok' : 'bg-warn'" :style="{ width: `${l.confianza * 100}%` }"></div>
                </div>
                {{ pct(l.confianza, 1) }}
              </div>
              <span v-else class="text-muted">Manual</span>
            </td>
            <td>{{ l.ms ? `${Math.round(l.ms)} ms` : '—' }}</td>
            <td>{{ l.registro ? ACTION[l.registro] : '—' }}</td>
          </tr>
          <tr v-if="!session.lecturas.length"><td colspan="7" class="text-center text-muted">Sin lecturas todavía. Elija una imagen o capture desde la cámara.</td></tr>
        </tbody>
      </table>
    </div>
</div><div class="mt-4 flex gap-2"><button class="btn-ghost" @click="exportLecturas">Exportar CSV</button><button class="btn-ghost" @click="session.clearLecturas()">Limpiar</button><button class="btn-primary" @click="readingsOpen = false">Cerrar</button></div></ModalDialog>
  <ModalDialog :open="manualOpen" title="Apertura manual (contingencia)" @close="manualOpen = false">
    <p class="mb-3 text-sm text-muted">
      Se abrirá la barrera para <b class="font-mono text-ink">{{ plateShown || 'placa sin leer' }}</b> en {{ session.garita }}.
      La apertura queda registrada con su usuario y el motivo.
    </p>
    <label class="field-label" for="motivo">Motivo (mín. 10 caracteres)</label>
    <textarea id="motivo" v-model="motivo" rows="3" maxlength="250" class="field" placeholder="Ej.: placa sucia, conductor identificado con credencial"></textarea>
    <div class="mt-4 flex justify-end gap-2">
      <button class="btn-ghost" @click="manualOpen = false">Cancelar</button>
      <button class="btn-navy" :disabled="motivo.trim().length < 10 || busy" @click="register('APERTURA_MANUAL')">Abrir y registrar</button>
    </div>
  </ModalDialog>
</template>
