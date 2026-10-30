<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '@/lib/api'
import AppIcon from '@/components/AppIcon.vue'
import VChart from 'vue-echarts'
import { baseOption, chartTheme } from '@/lib/charts'
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
const dark = computed(() => session.theme === 'dark')
const theme = computed(() => chartTheme(dark.value))
const percentValue = (value) => Number.isFinite(Number(value)) ? Number((Number(value) * 100).toFixed(1)) : 0

function percentBarChart(rows, color) {
  return {
    ...baseOption(dark.value),
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (items) => `${items[0]?.name || ''}: ${Number(items[0]?.value || 0).toFixed(1)}%`,
    },
    legend: { show: false },
    grid: { left: 132, right: 36, top: 14, bottom: 28 },
    xAxis: {
      type: 'value', min: 0, max: 100,
      axisLabel: { color: theme.value.text, formatter: '{value}%' },
      splitLine: { lineStyle: { color: theme.value.grid } },
    },
    yAxis: { type: 'category', data: rows.map((row) => row.label), axisLabel: { color: theme.value.text } },
    series: [{
      type: 'bar',
      data: rows.map((row) => percentValue(row.value)),
      barMaxWidth: 24,
      itemStyle: { color, borderRadius: [0, 6, 6, 0] },
      label: { show: true, position: 'right', formatter: '{c}%', color: theme.value.text, fontWeight: 700 },
    }],
  }
}
const detectorChart = computed(() => {
  const d = m.value.detector_test || {}
  return percentBarChart([
    { label: 'mAP@0.5', value: d.map50 },
    { label: 'mAP@0.5:0.95', value: d.map50_95 },
    { label: 'Precisión', value: d.precision },
    { label: 'Recall', value: d.recall },
    { label: 'F1', value: d.f1 },
  ], '#2156e8')
})
const plateSizeChart = computed(() => {
  const d = m.value.detector_test || {}
  return percentBarChart([
    { label: 'Pequeñas', value: d.map50_95_pequenas },
    { label: 'Medianas', value: d.map50_95_medianas },
    { label: 'Grandes', value: d.map50_95_grandes },
  ], '#0f766e')
})
const ocrChart = computed(() => {
  const o = m.value.ocr_savh || {}
  return percentBarChart([
    { label: 'Lectura exacta (EMR)', value: o.emr },
    { label: 'Formato válido', value: o.formato_valido },
  ], '#16a34a')
})
const latencyChart = computed(() => {
  const speed = m.value.velocidad || {}
  const ocr = m.value.ocr_savh || {}
  const e = m.value.e2e || {}
  const labels = ['Detector · GPU L4', 'OCR por recorte', 'Decisión completa']
  const values = [speed.latencia_ms_media, ocr.ms_por_recorte_media, e.tiempo_ms_promedio]
  return {
    ...baseOption(dark.value),
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: (items) => `${items[0]?.name || ''}: ${Number(items[0]?.value || 0).toFixed(1)} ms` },
    legend: { show: false },
    grid: { left: 132, right: 28, top: 16, bottom: 28 },
    xAxis: { type: 'value', min: 0, axisLabel: { color: theme.value.text, formatter: '{value} ms' }, splitLine: { lineStyle: { color: theme.value.grid } } },
    yAxis: { type: 'category', data: labels, axisLabel: { color: theme.value.text } },
    series: [{
      type: 'bar', data: values, barMaxWidth: 24,
      itemStyle: { color: '#d98a00', borderRadius: [0, 6, 6, 0] },
      label: { show: true, position: 'right', formatter: '{c} ms', color: theme.value.text, fontWeight: 700 },
    }],
  }
})
const optimizationChart = computed(() => {
  const comparison = opt.value.comparacion_test || {}
  const metrics = [['mAP@0.5', 'map50'], ['mAP@0.5:0.95', 'map50_95']]
  return {
    ...baseOption(dark.value),
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: (value) => `${Number(value).toFixed(1)}%` },
    legend: { bottom: 0, textStyle: { color: theme.value.text } },
    grid: { left: 112, right: 24, top: 18, bottom: 42 },
    xAxis: { type: 'value', min: 0, max: 100, axisLabel: { color: theme.value.text, formatter: '{value}%' }, splitLine: { lineStyle: { color: theme.value.grid } } },
    yAxis: { type: 'category', data: metrics.map(([label]) => label), axisLabel: { color: theme.value.text } },
    series: [
      { name: 'Base', type: 'bar', data: metrics.map(([, key]) => percentValue(comparison[key]?.base)), itemStyle: { color: '#94a3b8', borderRadius: [0, 5, 5, 0] } },
      { name: 'Optimizada', type: 'bar', data: metrics.map(([, key]) => percentValue(comparison[key]?.optimizada)), itemStyle: { color: '#2156e8', borderRadius: [0, 5, 5, 0] } },
    ],
  }
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
        <a href="mailto:eduardoceballos@yahoo.com" class="mt-1 inline-block text-base font-medium text-brand-600 hover:underline sm:text-lg">eduardoceballos@yahoo.com</a>
      </div>
      <div>
        <p class="text-2xl font-bold sm:text-3xl">Christian Xavier Valle Maridueña</p>
        <a href="mailto:cvalle130781@gmail.com" class="mt-1 inline-block text-base font-medium text-brand-600 hover:underline sm:text-lg">cvalle130781@gmail.com</a>
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

  <section class="mt-5" aria-labelledby="metrics-charts-heading">
    <h2 id="metrics-charts-heading" class="card-title">Gráficos de métricas y mediciones</h2>
    <div class="grid gap-5 xl:grid-cols-2">
      <section class="card">
        <h3 class="font-bold">Evaluación del detector YOLO11-s</h3>
        <p class="text-sm text-muted">Resultados del conjunto de prueba ({{ m.detector_test?.imagenes ?? '—' }} imágenes, {{ m.detector_test?.placas ?? '—' }} placas).</p>
        <VChart :option="detectorChart" autoresize style="height: 270px" />
      </section>
      <section class="card">
        <h3 class="font-bold">Detección según tamaño de placa</h3>
        <p class="text-sm text-muted">mAP@0.5:0.95; permite comparar la localización por tamaño.</p>
        <VChart :option="plateSizeChart" autoresize style="height: 230px" />
      </section>
      <section class="card">
        <h3 class="font-bold">Lectura OCR en placas de Guayaquil</h3>
        <p class="text-sm text-muted">SAVH, {{ m.ocr_savh?.n ?? '—' }} placas revisadas. CER: {{ pct(m.ocr_savh?.cer, 1) }} (menor es mejor).</p>
        <VChart :option="ocrChart" autoresize style="height: 210px" />
      </section>
      <section class="card">
        <h3 class="font-bold">Tiempo medido por etapa</h3>
        <p class="text-sm text-muted">Milisegundos; el tiempo completo corresponde a detección + OCR en el video de garita.</p>
        <VChart :option="latencyChart" autoresize style="height: 230px" />
      </section>
      <section class="card xl:col-span-2">
        <h3 class="font-bold">Comparación antes y después de Optuna</h3>
        <p class="text-sm text-muted">Métricas del conjunto de prueba; se muestra el modelo base y la configuración optimizada.</p>
        <VChart :option="optimizationChart" autoresize style="height: 230px" />
      </section>
    </div>
    <p class="mt-3 text-xs text-muted">Los valores se cargan desde los archivos de métricas del proyecto. En porcentajes, un valor más alto indica mejor resultado; el CER se informa aparte porque mide errores.</p>
  </section>

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
        <li>Una lectura con confianza OCR menor a {{ pct(info?.umbral_ocr ?? 0.94) }} <b>no</b> se decide sola: pasa a verificación manual.
          El operador confirma siempre; la barrera nunca se abre sin una acción humana.</li>
        <li>El EMR punta a punta en la garita real aún no se midió (falta la referencia anotada del video).</li>
        <li>Las imágenes de ejemplo derivan del diseño de la interfaz; no son capturas reales. La barrera de esta versión es
          <b>simulada</b> y la base de demostración contiene datos <b>ficticios</b> respaldados en el repositorio privado configurado.</li>
        <li>SIRAP <b>no</b> debe usarse para vigilancia masiva, rastreo de personas ni fines distintos al control de acceso de la
          instalación. Detalles en <code>docs/consideraciones_eticas.md</code>.</li>
      </ul>
    </section>
  </div>
</template>
