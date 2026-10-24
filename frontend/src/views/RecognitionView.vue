<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import ImageViewer from '@/components/ImageViewer.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import ResultCard from '@/components/ResultCard.vue'
import { api } from '@/lib/api'
import { RESULT, pct } from '@/lib/format'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'

const auth = useAuthStore()
const session = useSessionStore()

const source = ref('ejemplos')
const samples = ref([])
const selectedSample = ref('')
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
const motivo = ref('')

// --- cámara -----------------------------------------------------------------------------
const video = ref(null)
let stream = null
const cameraError = ref('')

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
  canvas.toBlob((blob) => { setImage(blob); recognize() }, 'image/jpeg', 0.92)
}
function setSource(name) {
  source.value = name
  if (name === 'camara') setTimeout(startCamera, 0)
  else stopCamera()
}
onBeforeUnmount(stopCamera)

// --- imagen -----------------------------------------------------------------------------
function reset() {
  recognition.value = null
  decision.value = null
  manualPlate.value = ''
  origin.value = 'DETECCION'
  done.value = false
}
function setImage(blob) {
  if (preview.value) URL.revokeObjectURL(preview.value)
  file.value = blob
  preview.value = URL.createObjectURL(blob)
  stamp.value = new Date().toLocaleString('es-EC')
  reset()
}
async function pickSample(name) {
  selectedSample.value = name
  const res = await api(`/api/samples/${name}`, { raw: true })
  setImage(await res.blob())
  await recognize()
}
async function onUpload(event) {
  const f = event.target.files?.[0]
  if (!f) return
  setImage(f)
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

onMounted(async () => {
  try {
    await session.loadSystem()
    samples.value = await api('/api/samples')
  } catch (e) {
    session.notify(e.message, 'bad')
  }
})
</script>

<template>
  <div class="grid gap-5 xl:grid-cols-12">
    <!-- Cámara / imagen -->
    <section class="card xl:col-span-7">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 class="card-title !mb-0"><span class="icon-chip"><AppIcon name="camera" /></span> Cámara ({{ session.garita || '—' }})</h2>
        <div class="flex rounded-xl bg-slate-100 p-1 text-sm font-semibold" role="tablist">
          <button v-for="s in [['ejemplos', 'Ejemplos'], ['subir', 'Subir imagen'], ['camara', 'Cámara']]" :key="s[0]"
                  class="rounded-lg px-3 py-1.5 transition" :class="source === s[0] ? 'bg-white shadow text-ink' : 'text-muted'"
                  role="tab" :aria-selected="source === s[0]" @click="setSource(s[0])">{{ s[1] }}</button>
        </div>
      </div>

      <div v-if="source === 'ejemplos'" class="mb-4 grid grid-cols-2 gap-2 lg:grid-cols-4">
        <button v-for="s in samples" :key="s.nombre" :disabled="loading"
                class="overflow-hidden rounded-xl border-2 text-left text-xs font-semibold transition hover:border-brand-500"
                :class="selectedSample === s.nombre ? 'border-brand-600' : 'border-transparent bg-slate-50'"
                @click="pickSample(s.nombre)">
          <img :src="s.url" alt="" class="aspect-video w-full object-cover" loading="lazy" />
          <span class="block px-2 py-1.5 leading-tight">{{ s.etiqueta }}</span>
        </button>
      </div>
      <label v-else-if="source === 'subir'"
             class="mb-4 flex cursor-pointer items-center justify-center gap-2 rounded-xl border-2 border-dashed border-slate-300 py-4 font-semibold text-muted hover:border-brand-500 hover:text-brand-600">
        <AppIcon name="upload" /> Elegir foto (JPG, PNG o WEBP · máx. 10 MB)
        <input type="file" accept="image/jpeg,image/png,image/webp" class="hidden" @change="onUpload" />
      </label>
      <div v-else class="mb-4">
        <video ref="video" autoplay playsinline muted class="max-h-72 w-full rounded-xl bg-navy-900 object-contain"></video>
        <p v-if="cameraError" class="mt-2 text-sm font-semibold text-bad">{{ cameraError }}</p>
        <button class="btn-primary mt-2 w-full" :disabled="loading" @click="capture"><AppIcon name="camera" /> Capturar y reconocer</button>
      </div>

      <ImageViewer :src="preview" :box="recognition?.box" :width="recognition?.image_width" :height="recognition?.image_height"
                   :tone="tone" :label="recognition?.plate" :garita="session.garita" :stamp="stamp" :loading="loading" />
      <p v-if="recognition" class="mt-3 text-xs text-muted">
        {{ recognition.detector }} · detección {{ recognition.timings_ms.deteccion?.toFixed(0) }} ms ·
        OCR {{ recognition.timings_ms.ocr?.toFixed(0) }} ms · total {{ recognition.timings_ms.total?.toFixed(0) }} ms
      </p>
    </section>

    <!-- Resultado y placa -->
    <section class="flex flex-col gap-5 xl:col-span-5">
      <ResultCard :decision="decision" :loading="loading" />
      <div class="card">
        <h2 class="card-title"><span class="icon-chip"><AppIcon name="car" /></span> PLACA IDENTIFICADA</h2>
        <div class="rounded-2xl border-[6px] border-ink bg-white px-4 py-3 text-center shadow-[inset_0_0_0_3px_#d7deea]">
          <p class="text-5xl font-black tracking-wide sm:text-6xl" :class="plateShown ? '' : 'text-slate-300'">
            {{ plateShown || '———-————' }}
          </p>
        </div>
        <div class="mt-3 flex items-center justify-between rounded-xl px-4 py-3 text-white"
             :class="{ ok: 'bg-ok-dark', bad: 'bg-bad', warn: 'bg-warn' }[tone] || 'bg-slate-400'">
          <span class="flex items-center gap-2 font-semibold"><AppIcon name="chart" /> Confianza OCR</span>
          <span class="text-3xl font-black">{{ origin === 'MANUAL' ? 'Manual' : pct(recognition?.ocr_confidence) }}</span>
        </div>
        <div v-if="recognition?.crop_jpeg_base64" class="mt-3 flex items-center gap-3 text-xs text-muted">
          <img :src="`data:image/jpeg;base64,${recognition.crop_jpeg_base64}`" alt="Recorte de la placa" class="h-12 rounded border" />
          <span>Recorte del detector · lectura cruda «{{ recognition.plate_raw || '—' }}» · det. {{ pct(recognition.det_confidence, 1) }}</span>
        </div>
        <form class="mt-4 flex gap-2" @submit.prevent="verifyManual">
          <input v-model.trim="manualPlate" class="field font-mono uppercase" placeholder="Corregir o escribir placa (ej. PBA-8901)" maxlength="12" />
          <button class="btn-ghost shrink-0" :disabled="busy || !manualPlate"><AppIcon name="edit" :size="18" /> Verificar</button>
        </form>
      </div>
    </section>

    <!-- Punto de control -->
    <section class="card xl:col-span-4">
      <h2 class="card-title"><span class="icon-chip"><AppIcon name="pin" /></span> Datos del punto de control</h2>
      <div class="grid grid-cols-[110px_1fr] items-center gap-3">
        <label class="font-medium" for="garita">Garita</label>
        <select id="garita" v-model="session.garita" class="field">
          <option v-for="g in session.system?.garitas || []" :key="g">{{ g }}</option>
        </select>
        <span class="font-medium">Operador</span>
        <div class="field bg-slate-100">{{ auth.user?.nombre }}</div>
        <label class="font-medium" for="mov">Operación</label>
        <select id="mov" v-model="session.movimiento" class="field">
          <option value="ENTRADA">Entrada</option>
          <option value="SALIDA">Salida</option>
        </select>
      </div>
    </section>

    <!-- Vehículo -->
    <section class="card xl:col-span-4">
      <h2 class="card-title"><span class="icon-chip"><AppIcon name="car" /></span> Detalles del vehículo</h2>
      <dl v-if="vehicle" class="space-y-1.5">
        <div v-for="[k, v] in [['Marca', vehicle.marca], ['Modelo', vehicle.modelo], ['Color', vehicle.color], ['Propietario', vehicle.propietario], ...(vehicle.transportista ? [['Transportista', vehicle.transportista]] : [])]"
             :key="k" class="grid grid-cols-[120px_1fr] rounded-lg bg-slate-50 px-3 py-2">
          <dt class="font-bold">{{ k }}:</dt><dd>{{ v || '—' }}</dd>
        </div>
      </dl>
      <p v-else class="rounded-lg bg-slate-50 px-3 py-6 text-center text-muted">
        {{ decision ? 'La placa no está registrada en la base.' : 'Sin vehículo identificado.' }}
      </p>
    </section>

    <!-- Acciones -->
    <section class="card xl:col-span-4">
      <h2 class="card-title"><span class="icon-chip"><AppIcon name="bolt" /></span> Acciones rápidas</h2>
      <div class="flex flex-col gap-2.5">
        <button class="btn-yellow py-3.5 text-lg" :disabled="!canOpen || busy" @click="register('APERTURA_AUTOMATICA')"
                :title="canOpen ? '' : 'Solo disponible cuando el resultado es AUTORIZADO'">
          <AppIcon name="barrier" :size="24" /> Registrar y Abrir Barrera
        </button>
        <button class="btn-red py-3.5 text-lg" :disabled="loading || !file" @click="recognize">
          <AppIcon name="settings" :size="22" /> Procesar detección automática
        </button>
        <button class="btn-navy py-3.5 text-lg" :disabled="!decision || busy || done" @click="manualOpen = true">
          <AppIcon name="lock" :size="22" /> Apertura manual (Contingencia)
        </button>
        <button v-if="decision && !decision.permite_apertura" class="btn-ghost" :disabled="busy || done"
                @click="register(decision.resultado === 'DENEGADO' ? 'RECHAZO' : 'SOLO_REGISTRO')">
          {{ decision.resultado === 'DENEGADO' ? 'Registrar rechazo (barrera cerrada)' : 'Registrar sin abrir' }}
        </button>
        <p v-if="done" class="text-center text-sm font-semibold text-ok-dark">✓ Lectura registrada en el historial.</p>
      </div>
    </section>
  </div>

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
