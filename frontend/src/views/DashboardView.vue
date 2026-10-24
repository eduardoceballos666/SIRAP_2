<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import VChart from 'vue-echarts'
import AppIcon from '@/components/AppIcon.vue'
import { api } from '@/lib/api'
import { ACTION } from '@/lib/format'
import { RESULT_COLORS, baseOption, chartTheme } from '@/lib/charts'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()
const dark = computed(() => session.theme === 'dark')
const theme = computed(() => chartTheme(dark.value))
const days = ref(7)
const includeDemo = ref(true)
const data = ref(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    data.value = await api('/api/dashboard', { params: { days: days.value, include_demo: includeDemo.value } })
  } catch (e) {
    session.notify(e.message, 'bad')
  } finally {
    loading.value = false
  }
}
watch([days, includeDemo], load)
onMounted(load)

const kpis = computed(() => {
  const k = data.value?.kpis || {}
  return [
    { label: 'Ingresos', value: k.ingresos ?? 0, icon: 'car', cls: 'bg-brand-600' },
    { label: 'Salidas', value: k.salidas ?? 0, icon: 'logout', cls: 'bg-navy-700' },
    { label: 'Placas identificadas', value: k.identificados ?? 0, icon: 'scan', cls: 'bg-ok-dark' },
    { label: 'Alertas', value: k.alertas ?? 0, icon: 'alert', cls: 'bg-bad' },
  ]
})

const hourly = computed(() => {
  const rows = data.value?.por_hora || []
  const hours = Array.from({ length: 24 }, (_, h) => h)
  const results = [...new Set(rows.map((r) => r.resultado))]
  return {
    ...baseOption(dark.value),
    xAxis: { type: 'category', data: hours.map((h) => `${String(h).padStart(2, '0')}h`), axisTick: { show: false }, axisLabel: { color: theme.value.text } },
    yAxis: { type: 'value', minInterval: 1, axisLabel: { color: theme.value.text }, splitLine: { lineStyle: { color: theme.value.grid } } },
    series: results.map((r) => ({
      name: r, type: 'bar', stack: 'total', barMaxWidth: 22, itemStyle: { color: RESULT_COLORS[r] },
      data: hours.map((h) => rows.find((x) => x.hora === h && x.resultado === r)?.n || 0),
    })),
  }
})

const byResult = computed(() => ({
  ...baseOption(dark.value),
  tooltip: { trigger: 'item' },
  series: [{
    type: 'pie', radius: ['52%', '78%'], center: ['50%', '42%'], itemStyle: { borderColor: theme.value.surface, borderWidth: 3 },
    label: { show: false }, tooltip: { formatter: '{b}: {c} ({d}%)' },
    data: (data.value?.por_resultado || []).map((r) => ({ name: r.resultado, value: r.n, itemStyle: { color: RESULT_COLORS[r.resultado] } })),
  }],
}))

const byGate = computed(() => {
  const rows = data.value?.por_garita || []
  const gates = [...new Set(rows.map((r) => r.garita))]
  return {
    ...baseOption(dark.value),
    xAxis: { type: 'category', data: gates, axisLabel: { color: theme.value.text } },
    yAxis: { type: 'value', minInterval: 1, axisLabel: { color: theme.value.text }, splitLine: { lineStyle: { color: theme.value.grid } } },
    series: [['ENTRADA', 'Entradas', '#2156e8'], ['SALIDA', 'Salidas', '#f7b900']].map(([m, name, color]) => ({
      name, type: 'bar', barMaxWidth: 34, itemStyle: { color, borderRadius: [6, 6, 0, 0] },
      data: gates.map((g) => rows.find((r) => r.garita === g && r.movimiento === m)?.n || 0),
    })),
  }
})
const empty = computed(() => data.value && !data.value.por_resultado.length)
</script>

<template>
  <div class="mb-4 flex flex-wrap items-center gap-3">
    <select v-model.number="days" class="field !w-auto">
      <option :value="1">Hoy</option>
      <option :value="7">Últimos 7 días</option>
      <option :value="30">Últimos 30 días</option>
    </select>
    <label class="flex items-center gap-2 text-sm font-medium">
      <input v-model="includeDemo" type="checkbox" class="h-4 w-4 accent-brand-600" /> Incluir operaciones de demostración
    </label>
    <button class="btn-ghost ml-auto" :disabled="loading" @click="load"><AppIcon name="refresh" :size="16" /> Actualizar</button>
  </div>

  <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
    <div v-for="k in kpis" :key="k.label" class="card flex items-center gap-4">
      <div class="grid h-12 w-12 place-items-center rounded-xl text-white" :class="k.cls"><AppIcon :name="k.icon" /></div>
      <div>
        <p class="text-sm font-semibold text-muted">{{ k.label }}</p>
        <p class="text-3xl font-black">{{ k.value }}</p>
      </div>
    </div>
  </div>

  <div v-if="empty" class="card mt-5 text-center text-muted">
    No hay operaciones en el periodo. Registre lecturas en «Reconocimiento y Acceso» o genere datos de demostración en Administración.
  </div>
  <div v-else class="mt-5 grid gap-5 xl:grid-cols-3">
    <section class="card xl:col-span-2">
      <h2 class="card-title">Operaciones por hora</h2>
      <VChart :option="hourly" autoresize style="height: 300px" />
    </section>
    <section class="card">
      <h2 class="card-title">Resultado de acceso</h2>
      <VChart :option="byResult" autoresize style="height: 300px" />
    </section>
    <section class="card">
      <h2 class="card-title">Movimientos por garita</h2>
      <VChart :option="byGate" autoresize style="height: 300px" />
    </section>
    <section class="card xl:col-span-2">
      <h2 class="card-title"><span class="icon-chip !bg-bad"><AppIcon name="alert" /></span> Alertas recientes</h2>
      <div class="table-wrap max-h-80">
        <table class="tbl">
          <thead><tr><th>Fecha y hora</th><th>Garita</th><th>Placa</th><th>Resultado</th><th>Acción</th><th>Operador</th></tr></thead>
          <tbody>
            <tr v-for="(a, i) in data?.alertas || []" :key="i">
              <td>{{ a.fecha_hora }}</td><td>{{ a.garita }}</td><td class="font-mono font-bold">{{ a.placa_final || '—' }}</td>
              <td>{{ a.resultado_txt }}</td><td>{{ ACTION[a.accion] || a.accion }}</td><td>{{ a.operador }}</td>
            </tr>
            <tr v-if="!data?.alertas?.length"><td colspan="6" class="text-center text-muted">Sin alertas.</td></tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
