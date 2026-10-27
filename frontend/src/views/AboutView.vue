<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '@/lib/api'
import AppIcon from '@/components/AppIcon.vue'
import { num, pct } from '@/lib/format'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()
const info = ref(null)
onMounted(async () => {
  try { info.value = await api('/api/model/info') } catch (e) { session.notify(e.message, 'bad') }
})
const m = computed(() => info.value?.metricas || {})
const cards = computed(() => {
  const d = m.value.detector_test || {}, o = m.value.ocr_savh || {}, e = m.value.e2e || {}
  return [
    { label: 'mAP@0.5 (test)', value: num(d.map50), sub: `${d.imagenes ?? '—'} imágenes · ${d.placas ?? '—'} placas` },
    { label: 'mAP@0.5:0.95', value: num(d.map50_95), sub: 'Detector YOLO11-s' },
    { label: 'Precisión / Recall', value: `${num(d.precision, 3)} / ${num(d.recall, 3)}`, sub: `F1 ${num(d.f1)}` },
    { label: 'Exactitud OCR (SAVH)', value: pct(o.emr, 1), sub: `${o.n ?? '—'} placas de Guayaquil · CER ${pct(o.cer, 1)}` },
    { label: 'Tiempo por decisión', value: e.tiempo_ms_promedio ? `${Math.round(e.tiempo_ms_promedio)} ms` : '—', sub: 'Detección + OCR (meta < 1 s)' },
    { label: 'Umbral del detector', value: num(m.value.umbrales?.YOLO11?.conf, 2), sub: 'Calibrado en validación' },
  ]
})
const tr = computed(() => m.value.entrenamiento || {})
const ft = computed(() => m.value.ocr_afinamiento || {})
const opt = computed(() => m.value.optimizacion_resumen || {})
</script>

<template>
  <section class="card mb-5" aria-labelledby="developers-heading">
    <h2 id="developers-heading" class="card-title">Desarrolladores</h2>
    <div class="space-y-4 leading-snug break-words">
      <div>
        <p class="text-2xl font-bold sm:text-3xl">Eduardo Alejandro Ceballos Jijon</p>
        <p class="text-base text-muted sm:text-lg">eduardoceballos@yahoo.com</p>
      </div>
      <div>
        <p class="text-2xl font-bold sm:text-3xl">Christian Xavier Valle Maridueña</p>
        <p class="text-base text-muted sm:text-lg">cvalle130781@gmail.com</p>
      </div>
    </div>
  </section>

  <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
    <div v-for="c in cards" :key="c.label" class="card">
      <p class="text-sm font-semibold text-muted">{{ c.label }}</p>
      <p class="mt-1 text-3xl font-black">{{ c.value }}</p>
      <p class="mt-1 text-sm text-muted">{{ c.sub }}</p>
    </div>
  </div>

  <div class="mt-5 grid gap-5 xl:grid-cols-2">
    <section class="card space-y-3 leading-relaxed">
      <h2 class="card-title">Cómo funciona</h2>
      <ol class="list-decimal space-y-2 pl-5">
        <li><b>Detección:</b> {{ info?.detector || 'YOLO11-s' }} localiza la placa en la imagen.</li>
        <li><b>Lectura:</b> {{ info?.ocr || 'fast-plate-ocr' }} lee los caracteres del recorte; la confianza es la probabilidad mínima por carácter.</li>
        <li><b>Normalización:</b> se corrigen confusiones típicas (O↔0, I↔1, S↔5…) y se valida el formato ecuatoriano <code>XXX-0000</code>.</li>
        <li><b>Decisión:</b> la placa se busca en la base: lista blanca → <b class="text-ok-dark">Autorizado</b>, lista restringida → <b class="text-bad">Denegado</b>, sin registro → <b class="text-warn">No registrado</b>; confianza baja → <b class="text-warn">Verificación manual</b>.</li>
        <li><b>Registro:</b> el operador confirma; cada operación queda en el historial con usuario, garita y hora. La barrera está simulada.</li>
      </ol>
    </section>
    <section class="card space-y-3 leading-relaxed">
      <h2 class="card-title">Entrenamiento y validación</h2>
      <p>YOLO11-s entrenado {{ tr.epocas_corridas ?? '—' }} épocas (imgsz {{ tr.imgsz ?? 640 }}, batch {{ tr.batch ?? 16 }},
        {{ tr.optimizer || 'AdamW' }}) sobre <i>{{ tr.dataset || 'license-plate-recognition' }}</i>, en {{ num(tr.horas, 2) }} h de GPU.</p>
      <p v-if="opt.comparacion_test">Optimización de hiperparámetros (Optuna, 24 <i>trials</i>): <code>lr0</code> fue el factor dominante.
        Con <code>lr0</code> ≈ {{ opt.mejor_config?.lr0?.toExponential(1) }} el mAP@0.5:0.95 de <i>test</i> pasa de
        {{ num(opt.comparacion_test.map50_95?.base) }} a {{ num(opt.comparacion_test.map50_95?.optimizada) }} con el mismo mAP@0.5;
        se mantiene el modelo entregado (detalles en <code>docs/optimizacion.md</code>).</p>
      <p>El OCR se evaluó con placas reales de Guayaquil (SAVH). Un afinamiento con placas ecuatorianas
        ({{ ft.particion?.train ?? '—' }} recortes de entrenamiento) no mejoró de forma significativa
        (EMR {{ pct(ft.original?.emr, 1) }} original), por lo que se mantiene el modelo preentrenado.</p>
      <p class="text-sm text-muted">Las métricas provienen de <code>results/metrics/*.json</code>, generadas por los notebooks del repositorio.</p>
    </section>
    <section class="card space-y-3 leading-relaxed xl:col-span-2 border-l-4 border-warn">
      <h2 class="card-title"><span class="icon-chip !bg-warn"><AppIcon name="alert" /></span> Limitaciones y advertencias</h2>
      <ul class="list-disc space-y-1.5 pl-5">
        <li>El detector se entrenó con placas de varios países; no es específico de Ecuador. El OCR se validó con placas reales
          de <b>SAVH Guayaquil</b>, pero rinde menos con placas sucias, dañadas, de noche, muy inclinadas o lejanas
          (mAP@0.5:0.95 de placas pequeñas: {{ num(m.detector_test?.map50_95_pequenas) }}).</li>
        <li>Una lectura con confianza OCR menor a {{ pct(info?.umbral_ocr ?? 0.99) }} <b>no</b> se decide sola: pasa a verificación manual.
          El operador confirma siempre; la barrera nunca se abre sin una acción humana.</li>
        <li>El EMR punta a punta en la garita real aún no se midió (falta la referencia anotada del video).</li>
        <li>Las imágenes de ejemplo derivan del diseño de la interfaz; no son capturas reales. La barrera de esta versión es
          <b>simulada</b> y la base de demostración contiene datos <b>ficticios</b> que se borran al reiniciar el servidor.</li>
        <li>SIRAP <b>no</b> debe usarse para vigilancia masiva, rastreo de personas ni fines distintos al control de acceso de la
          instalación. Detalles en <code>docs/consideraciones_eticas.md</code>.</li>
      </ul>
    </section>
  </div>
</template>
