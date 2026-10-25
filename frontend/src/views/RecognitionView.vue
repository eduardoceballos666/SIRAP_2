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
const currentReadingIds = ref([])
const file = ref(null) // imagen que se enviará al reconocimiento
const preview = ref('')
const stamp = ref('')
const mediaUrl = ref('')
const mediaKind = ref('image')
const mediaReady = ref(false)
const uploadedVideoName = ref('')
const onlineUrlDraft = ref('')
const onlineUrl = ref('')
const onlineMode = ref('video')
const onlineConnected = ref(false)
const imagePreviewVisible = computed(() => source.value === 'ejemplos' || (source.value === 'subir' && mediaKind.value === 'image') || showCapture.value)
const hasActiveVideo = computed(() => source.value === 'camara' || (source.value === 'subir' && mediaKind.value === 'video') || (source.value === 'online' && onlineConnected.value))

const loading = ref(false)
const recognition = ref(null)
const detection = ref(null)
const ocrAttempt = ref(null)
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
const mediaVideo = ref(null)
const networkImage = ref(null)
let stream = null
let analysisTimer = null
let framePending = false
const continuousAnalysis = ref(false)
const cameraError = ref('')
const confirmedFrames = ref(0)
const analysisMessage = ref('')
let pendingPlate = ''
let pendingPlateFrames = 0
let pendingPlateAt = 0
let videoPlaybackEnded = false

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
  mediaReady.value = false
  try {
    if (!navigator.mediaDevices?.getUserMedia) throw new Error('getUserMedia no disponible')
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment', width: { ideal: 1280 } } })
    if (video.value) video.value.srcObject = stream
  } catch {
    cameraError.value = 'No se pudo acceder a la cámara local. Verifique el permiso del navegador y use HTTPS o localhost.'
  }
}
function stopCamera() {
  stream?.getTracks().forEach((t) => t.stop())
  stream = null
}
function stopContinuousAnalysis() {
  if (analysisTimer) clearInterval(analysisTimer)
  analysisTimer = null
  continuousAnalysis.value = false
}
function clearPlateConfirmation() {
  pendingPlate = ''
  pendingPlateFrames = 0
  pendingPlateAt = 0
  confirmedFrames.value = 0
}
function finishVideoAnalysis() {
  stopContinuousAnalysis()
  if (!recognition.value) {
    analysisMessage.value = 'El video terminó sin confirmar la misma placa en dos cuadros con confianza ≥94 %. Verifique la placa manualmente.'
    session.notify(analysisMessage.value, 'warn')
  }
}
function videoEnded() {
  videoPlaybackEnded = true
  if (!loading.value) finishVideoAnalysis()
}
function activeMediaElement() {
  if (source.value === 'camara') return video.value
  if (source.value === 'online' && onlineMode.value === 'mjpeg') return networkImage.value
  if ((source.value === 'subir' && mediaKind.value === 'video') || (source.value === 'online' && onlineMode.value === 'video')) return mediaVideo.value
  return null
}
function mediaLoaded() {
  mediaReady.value = true
  cameraError.value = ''
  // MJPEG entrega fotogramas como imágenes: iniciar el análisis al llegar el primero.
  if (source.value === 'online' && onlineMode.value === 'mjpeg') startAutomaticAnalysis()
}
function mediaPlaying() {
  mediaLoaded()
  startAutomaticAnalysis()
}
function startAutomaticAnalysis() {
  if (continuousAnalysis.value || !mediaReady.value) return
  clearPlateConfirmation()
  videoPlaybackEnded = false
  analysisMessage.value = ''
  showCapture.value = false
  continuousAnalysis.value = true
  captureFrame({ freeze: false })
  analysisTimer = setInterval(() => {
    if (continuousAnalysis.value && mediaReady.value && !loading.value && !framePending) captureFrame({ freeze: false })
  }, 1000)
}
function mediaFailed() {
  mediaReady.value = false
  cameraError.value = source.value === 'online'
    ? 'No se pudo reproducir el enlace. Use una URL HTTP/HTTPS compatible con el navegador.'
    : 'No se pudo reproducir este video. Pruebe un archivo MP4 o WebM.'
}
function frameLabel(media) {
  const time = Number.isFinite(media?.currentTime) && media.currentTime > 0
    ? new Date(Math.floor(media.currentTime) * 1000).toISOString().slice(14, 19)
    : new Date().toLocaleTimeString('es-EC')
  if (source.value === 'camara') return `Cámara local · ${time}`
  if (source.value === 'online') return `Cámara en línea · ${time}`
  return `${uploadedVideoName.value || 'Video'} · ${time}`
}
function captureFrame({ freeze = true } = {}) {
  if (framePending || loading.value) return
  const media = activeMediaElement()
  const width = media?.videoWidth || media?.naturalWidth
  const height = media?.videoHeight || media?.naturalHeight
  if (!mediaReady.value || !width || !height) {
    session.notify('Espere a que el video esté reproduciéndose antes de analizar un fotograma.', 'warn')
    return
  }
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const label = frameLabel(media)
  try {
    const context = canvas.getContext('2d')
    context.drawImage(media, 0, 0, width, height)
    framePending = true
    canvas.toBlob((blob) => {
      framePending = false
      if (!blob) {
        session.notify('No se pudo leer el fotograma. La cámara en línea debe permitir acceso CORS para analizarla.', 'bad')
        return
      }
      setImage(blob, label)
      if (freeze) showCapture.value = true
      recognize()
    }, 'image/jpeg', 0.92)
  } catch {
    framePending = false
    session.notify('El navegador no permite leer fotogramas de esta cámara. Verifique CORS o use una fuente local/HTTPS compatible.', 'bad')
  }
}
function capture() {
  captureFrame({ freeze: true })
}
function toggleContinuousAnalysis() {
  if (continuousAnalysis.value) {
    stopContinuousAnalysis()
    return
  }
  if (!mediaReady.value) {
    session.notify('Espere a que el video o la cámara esté listo para analizar.', 'warn')
    return
  }
  startAutomaticAnalysis()
}
function connectOnlineCamera() {
  let parsed
  try {
    parsed = new URL(onlineUrlDraft.value.trim())
  } catch {
    session.notify('Ingrese una URL válida de cámara.', 'warn')
    return
  }
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    session.notify('Use una URL HTTP/HTTPS reproducible en el navegador. RTSP requiere un servidor puente.', 'warn')
    return
  }
  stopContinuousAnalysis()
  stopCamera()
  source.value = 'online'
  onlineUrl.value = parsed.href
  onlineUrlDraft.value = parsed.href
  onlineConnected.value = true
  showCapture.value = false
  mediaReady.value = false
  cameraError.value = ''
  sourceLabel.value = 'Cámara en línea'
  reset()
}
function setSource(name) {
  stopContinuousAnalysis()
  clearPlateConfirmation()
  videoPlaybackEnded = false
  analysisMessage.value = ''
  source.value = name
  detection.value = null
  showCapture.value = false
  mediaReady.value = false
  cameraError.value = ''
  if (name === 'camara') setTimeout(startCamera, 0)
  else stopCamera()
}
onBeforeUnmount(() => {
  stopContinuousAnalysis()
  stopCamera()
  if (preview.value) URL.revokeObjectURL(preview.value)
  if (mediaUrl.value) URL.revokeObjectURL(mediaUrl.value)
  clearInterval(clockTimer)
  document.removeEventListener('fullscreenchange', syncFullscreen)
})

// --- imagen -----------------------------------------------------------------------------
function reset() {
  recognition.value = null
  detection.value = null
  ocrAttempt.value = null
  decision.value = null
  manualPlate.value = ''
  origin.value = 'DETECCION'
  done.value = false
  registrationPromptDismissed.value = false
  lecturaId.value = null
  currentReadingIds.value = []
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
  stopContinuousAnalysis()
  session.clearUnregisteredLecturas(currentReadingIds.value)
  if (preview.value) URL.revokeObjectURL(preview.value)
  if (mediaUrl.value) URL.revokeObjectURL(mediaUrl.value)
  preview.value = ''
  mediaUrl.value = ''
  uploadedVideoName.value = ''
  if (source.value === 'subir') mediaKind.value = 'image'
  if (source.value === 'online') {
    onlineConnected.value = false
    onlineUrl.value = ''
    onlineUrlDraft.value = ''
  }
  if (source.value === 'subir' || source.value === 'online') mediaReady.value = false
  file.value = null
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
  const isVideo = f.type.startsWith('video/') || /\.(mp4|webm|mov|m4v|ogv|ogg)$/i.test(f.name)
  stopContinuousAnalysis()
  clearPlateConfirmation()
  videoPlaybackEnded = false
  analysisMessage.value = ''
  mediaReady.value = false
  showCapture.value = false
  if (mediaUrl.value) URL.revokeObjectURL(mediaUrl.value)
  mediaUrl.value = ''
  uploadedVideoName.value = ''
  if (isVideo) {
    if (preview.value) URL.revokeObjectURL(preview.value)
    preview.value = ''
    file.value = null
    mediaKind.value = 'video'
    uploadedVideoName.value = f.name
    mediaUrl.value = URL.createObjectURL(f)
    sourceLabel.value = f.name
    stamp.value = new Date().toLocaleString('es-EC')
    reset()
  } else {
    mediaKind.value = 'image'
    setImage(f, f.name)
    await recognize()
  }
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
    detection.value = data.recognition
    ocrAttempt.value = { confidence: Number(data.recognition.ocr_confidence) || 0, hasPlate: Boolean(data.recognition.plate) }
    const accepted = Boolean(data.recognition.plate) && Number(data.recognition.ocr_confidence) >= 0.94
    if (continuousAnalysis.value) {
      const candidate = String(data.recognition.plate || '').replace(/[^A-Z0-9]/gi, '').toUpperCase()
      const nowMs = Date.now()
      if (accepted && candidate) {
        if (candidate !== pendingPlate || nowMs - pendingPlateAt > 7500) {
          pendingPlate = candidate
          pendingPlateFrames = 1
        } else {
          pendingPlateFrames += 1
        }
        pendingPlateAt = nowMs
        confirmedFrames.value = pendingPlateFrames
        if (pendingPlateFrames < 2) return
      } else {
        confirmedFrames.value = pendingPlateFrames
        return
      }
    }
    if (!accepted) return

    // En video/cámara, la misma placa debe superar 94 % en dos cuadros muestreados.
    recognition.value = data.recognition
    if (continuousAnalysis.value) stopContinuousAnalysis()
    decision.value = data.decision
    manualPlate.value = data.recognition.plate
    session.addLectura({
      fuente: sourceLabel.value || 'Imagen', placa: data.recognition.plate, resultado: data.decision.resultado,
      confianza: data.recognition.ocr_confidence, ms: data.recognition.timings_ms?.total, origen: 'DETECCION',
    })
    lecturaId.value = session.lecturas[0].id
    currentReadingIds.value.push(lecturaId.value)
  } catch (e) {
    session.notify(e.message, 'bad')
  } finally {
    loading.value = false
    if (videoPlaybackEnded && !recognition.value) finishVideoAnalysis()
  }
}

function processCurrentMedia() {
  if (hasActiveVideo.value && mediaReady.value) captureFrame({ freeze: true })
  else recognize()
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
    currentReadingIds.value.push(lecturaId.value)
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
            <button v-for="s in [['camara', 'En vivo'], ['ejemplos', 'Ejemplos'], ['subir', 'Subir archivo'], ['online', 'Cámara URL']]" :key="s[0]" :aria-pressed="source === s[0]" :class="{ active: source === s[0] }" @click="setSource(s[0])">{{ s[1] }}</button>
          </div>
          <button class="btn-ghost fullscreen-button" :aria-label="fullscreen ? 'Salir de pantalla completa' : 'Ver en pantalla completa'" :title="fullscreen ? 'Salir de pantalla completa' : 'Ver en pantalla completa'" @click="toggleFullscreen">
            <AppIcon :name="fullscreen ? 'minimize' : 'fullscreen'" :size="17" /><span>{{ fullscreen ? 'Salir' : 'Pantalla completa' }}</span>
          </button>
        </div>

        <select v-if="source === 'ejemplos'" :value="selectedSample" class="field sample-select" aria-label="Probar con un ejemplo" :disabled="loading" @change="pickSample($event.target.value)">
          <option disabled value="">Seleccionar imagen de ejemplo…</option><option v-for="s in samples" :key="s.nombre" :value="s.nombre">{{ s.etiqueta }}</option>
        </select>
        <div v-else-if="source === 'subir'" class="media-source-tools">
          <label class="upload-compact"><AppIcon name="upload" :size="17" /><span>{{ mediaKind === 'video' ? 'Cambiar archivo' : 'Elegir imagen o video' }} · JPG, PNG, WEBP, MP4 o WEBM</span><input type="file" accept="image/jpeg,image/png,image/webp,video/*" class="hidden" @change="onUpload" /></label>
          <div v-if="mediaKind === 'video'" class="live-camera-tools">
            <button class="btn-primary" :disabled="!mediaReady || loading" @click="captureFrame({ freeze: true })"><AppIcon name="scan" :size="16" /> Analizar fotograma</button>
            <button class="btn-ghost" :disabled="!mediaReady || loading" @click="toggleContinuousAnalysis">{{ continuousAnalysis ? 'Detener análisis' : 'Analizar cada 2,5 s' }}</button>
            <button v-if="showCapture" class="btn-ghost" @click="showCapture = false">Volver al video</button>
          </div>
        </div>
        <div v-else-if="source === 'online'" class="online-source-tools">
          <form class="online-camera-form" @submit.prevent="connectOnlineCamera">
            <select v-model="onlineMode" class="field" aria-label="Formato de la cámara en línea"><option value="video">Video web (MP4/WebM)</option><option value="mjpeg">MJPEG</option></select>
            <input v-model.trim="onlineUrlDraft" class="field" aria-label="URL de cámara en línea" placeholder="https://dirección-de-cámara/video" />
            <button class="btn-primary" :disabled="!onlineUrlDraft.trim()">Conectar</button>
          </form>
          <p class="camera-stream-hint">Use una URL HTTP/HTTPS compatible con el navegador (MP4/WebM o MJPEG). HLS solo funciona donde el navegador lo admite; RTSP requiere un servidor puente. Para analizar fuentes externas, habilite CORS.</p>
          <div v-if="onlineConnected" class="live-camera-tools">
            <button class="btn-primary" :disabled="!mediaReady || loading" @click="captureFrame({ freeze: true })"><AppIcon name="scan" :size="16" /> Analizar fotograma</button>
            <button class="btn-ghost" :disabled="!mediaReady || loading" @click="toggleContinuousAnalysis">{{ continuousAnalysis ? 'Detener análisis' : 'Analizar cada 2,5 s' }}</button>
            <button v-if="showCapture" class="btn-ghost" @click="showCapture = false">Volver al video</button>
          </div>
        </div>
        <div v-else class="live-camera-tools">
          <button class="btn-primary" :disabled="!mediaReady || loading" @click="capture"><AppIcon name="camera" :size="16" /> Capturar y reconocer</button>
          <button class="btn-ghost" :disabled="!mediaReady || loading" @click="toggleContinuousAnalysis">{{ continuousAnalysis ? 'Detener análisis' : 'Analizar cada 2,5 s' }}</button>
          <button v-if="showCapture" class="btn-ghost" @click="showCapture = false">Volver a cámara en vivo</button>
        </div>

        <p v-if="cameraError" role="alert" class="camera-error">{{ cameraError }}</p>
        <div class="camera-stage">
          <video v-if="source === 'camara'" v-show="!showCapture" ref="video" autoplay playsinline muted @loadedmetadata="mediaLoaded" @playing="mediaPlaying" @error="mediaFailed"></video>
          <video v-else-if="source === 'subir' && mediaKind === 'video'" v-show="!showCapture" ref="mediaVideo" :src="mediaUrl" controls autoplay playsinline muted @loadedmetadata="mediaLoaded" @playing="mediaPlaying" @ended="videoEnded" @error="mediaFailed"></video>
          <template v-else-if="source === 'online' && onlineConnected">
            <video v-if="onlineMode === 'video'" v-show="!showCapture" ref="mediaVideo" :src="onlineUrl" controls autoplay playsinline muted @loadedmetadata="mediaLoaded" @playing="mediaPlaying" @error="mediaFailed"></video>
            <img v-else v-show="!showCapture" ref="networkImage" :src="onlineUrl" alt="Video en vivo de cámara en línea" @load="mediaLoaded" @error="mediaFailed" />
          </template>
          <ImageViewer v-show="imagePreviewVisible" class="compact-viewer" :src="preview" :width="detection?.image_width" :height="detection?.image_height" :tone="tone" :label="recognition?.plate" :garita="session.garita" :stamp="stamp" :loading="loading" />
        </div>
        <section class="rounded-xl border border-line bg-surface px-3 py-2" aria-label="Análisis OCR" aria-live="polite">
          <div class="flex items-center justify-between gap-2">
            <strong class="text-xs uppercase text-ink">Análisis OCR</strong>
            <span class="text-xs font-semibold text-brand-700">{{ analysisMessage || (loading ? 'Analizando fotograma…' : recognition ? 'Lectura confirmada en dos cuadros' : ocrAttempt ? (ocrAttempt.hasPlate && ocrAttempt.confidence >= 0.94 && continuousAnalysis ? 'Confirmando la misma placa: ' + confirmedFrames + '/2 cuadros' : ocrAttempt.hasPlate ? 'Buscando confianza ≥94 %' : 'No se leyó placa; continúa el análisis') : 'Esperando imagen o video') }}</span>
          </div>
          <div class="mt-1 h-2 overflow-hidden rounded-full bg-subtle-2" role="progressbar" :aria-valuenow="Math.round((ocrAttempt?.confidence || 0) * 100)" aria-valuemin="0" aria-valuemax="100" aria-label="Confianza OCR actual">
            <i class="block h-full rounded-full bg-brand-600 transition-all" :style="{ width: Math.max(0, Math.min(100, (ocrAttempt?.confidence || 0) * 100)) + '%' }"></i>
          </div>
          <p class="mt-1 text-[10px] text-muted">{{ ocrAttempt ? 'Confianza OCR: ' + pct(ocrAttempt.confidence) + ' · la placa y el resultado se muestran solo desde 94 %' : 'El sistema seguirá analizando hasta alcanzar 94 % de confianza.' }}</p>
        </section>
        <div class="camera-meta">
          <span>{{ detection ? detection.detector + (recognition ? ' · ' + recognition.timings_ms.total?.toFixed(0) + ' ms' : ' · confirmando OCR ≥94 % en dos cuadros') : sourceLabel || 'Seleccione una imagen o fuente de video' }}</span>
          <div class="camera-meta-actions">
            <button class="btn-ghost clear-reading-button" :disabled="loading || busy || (!file && !preview && !mediaUrl && !onlineConnected && !decision && !manualPlate)" @click="clearCurrentReading"><AppIcon name="trash" :size="14" /> Limpiar lectura</button>
            <button class="btn-ghost" :disabled="loading || (!file && !mediaReady)" @click="processCurrentMedia"><AppIcon name="refresh" :size="15" /> Reprocesar</button>
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
        <section class="card plate-panel" aria-label="Placa identificada">
          <div class="section-heading"><h2><AppIcon name="camera" :size="19" /> Placa identificada</h2><span>{{ origin === 'MANUAL' ? 'Manual' : 'OCR' }}</span></div>
          <div class="plate-line"><div class="compact-plate">{{ plateShown || '———-————' }}</div></div>
          <form class="plate-form" @submit.prevent="verifyManual"><input v-model.trim="manualPlate" class="field font-mono uppercase" aria-label="Corregir o escribir placa" placeholder="Corregir / escribir placa" maxlength="12" /><button class="btn-ghost" :disabled="busy || !manualPlate">Verificar</button></form>
        </section>

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
      <button class="btn-red action-button" :disabled="loading || (!file && !mediaReady)" @click="processCurrentMedia"><AppIcon name="settings" :size="20" /><span>Procesar detección automática</span></button>
      <button class="btn-navy action-button" :disabled="!decision || busy || done" @click="manualOpen = true"><AppIcon name="lock" :size="19" /><span>Apertura manual (Contingencia)</span></button>
    </div>
  </div>
  <ModalDialog :open="helpOpen" title="Cómo registrar un acceso" @close="helpOpen = false"><ol class="list-decimal space-y-3 pl-5"><li>Elija un ejemplo, suba una imagen o video, o conecte una cámara local o una URL compatible.</li><li>Las imágenes se analizan al seleccionarlas. Los videos y cámaras se analizan automáticamente cada 1 segundo hasta leer una placa válida con al menos 94 % de confianza OCR; las lecturas inferiores no se muestran.</li><li>Revise la placa, el vehículo y el resultado. Corrija la placa y pulse Verificar si es necesario.</li><li>Autorice y abra solo cuando el resultado lo permita, o registre sin abrir. La apertura manual requiere un motivo.</li><li>Las lecturas solo se guardan en el historial al registrar una acción.</li></ol><button class="btn-primary mt-4" @click="helpOpen = false">Entendido</button></ModalDialog>
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
