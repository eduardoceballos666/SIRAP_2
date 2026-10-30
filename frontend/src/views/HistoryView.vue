<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import { api, getToken } from '@/lib/api'
import { ACTION, RESULT, TONE_PILL, pct, today } from '@/lib/format'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'

const auth = useAuthStore()
const session = useSessionStore()
const filters = reactive({ desde: today(-6), hasta: today(), placa: '', garita: '', resultado: '', tipo_movimiento: '' })
const rows = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    rows.value = await api('/api/operations', { params: filters })
  } catch (e) {
    session.notify(e.message, 'bad')
  } finally {
    loading.value = false
  }
}
async function exportCsv() {
  try {
    const res = await api('/api/operations/export.csv', { params: filters, raw: true })
    const url = URL.createObjectURL(await res.blob())
    const a = Object.assign(document.createElement('a'), { href: url, download: `sirap_historial_${today()}.csv` })
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    session.notify(e.message, 'bad')
  }
}
const canExport = computed(() => auth.hasRole('SUPERVISOR', 'ADMINISTRADOR') && Boolean(getToken()))
onMounted(async () => {
  await session.loadSystem().catch(() => {})
  load()
})
</script>

<template>
  <section class="card mb-5">
    <form class="grid gap-3 sm:grid-cols-2 lg:grid-cols-7" @submit.prevent="load">
      <div><label class="field-label">Desde</label><input v-model="filters.desde" type="date" class="field" /></div>
      <div><label class="field-label">Hasta</label><input v-model="filters.hasta" type="date" class="field" /></div>
      <div><label class="field-label">Placa</label><input v-model.trim="filters.placa" class="field font-mono uppercase" placeholder="PBA-8901" /></div>
      <div>
        <label class="field-label">Garita</label>
        <select v-model="filters.garita" class="field"><option value="">Todas</option>
          <option v-for="g in session.system?.garitas || []" :key="g">{{ g }}</option></select>
      </div>
      <div>
        <label class="field-label">Resultado</label>
        <select v-model="filters.resultado" class="field"><option value="">Todos</option>
          <option v-for="(v, k) in RESULT" :key="k" :value="k">{{ v.label }}</option></select>
      </div>
      <div>
        <label class="field-label">Movimiento</label>
        <select v-model="filters.tipo_movimiento" class="field"><option value="">Todos</option>
          <option value="ENTRADA">Entrada</option><option value="SALIDA">Salida</option></select>
      </div>
      <div class="flex items-end gap-2">
        <button class="btn-primary flex-1" :disabled="loading"><AppIcon name="search" :size="18" /> Buscar</button>
      </div>
    </form>
  </section>

  <section class="card">
    <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
      <p class="font-semibold">{{ rows.length }} operaciones</p>
      <button v-if="canExport" class="btn-ghost" @click="exportCsv"><AppIcon name="download" :size="18" /> Exportar CSV</button>
    </div>
    <div class="table-wrap max-h-[65vh]">
      <table class="tbl">
        <thead><tr><th>Fecha y hora</th><th>Garita</th><th>Mov.</th><th>Placa leída</th><th>Placa final</th><th>Conf. OCR</th>
          <th>Resultado</th><th>Acción</th><th>Estado barrera</th><th>ID operación</th><th>Lista</th><th>Operador</th><th>Origen</th><th>Motivo</th></tr></thead>
        <tbody>
          <tr v-for="r in rows" :key="r.id">
            <td>{{ r.fecha_hora }}</td><td>{{ r.garita }}</td><td>{{ r.tipo_movimiento === 'ENTRADA' ? 'Entrada' : 'Salida' }}</td>
            <td class="font-mono">{{ r.placa_leida || '—' }}</td><td class="font-mono font-bold">{{ r.placa_final || '—' }}</td>
            <td>{{ pct(r.confianza_ocr, 1) }}</td>
            <td><span class="pill" :class="TONE_PILL[RESULT[r.resultado]?.tone]">{{ RESULT[r.resultado]?.label || r.resultado }}</span></td>
            <td>{{ ACTION[r.accion] || r.accion }}</td>
            <td :title="r.estado_barrera || ''"><span :class="r.estado_barrera === 'INDETERMINADA' || r.estado_barrera === 'SOLICITADA' ? 'font-bold text-warn' : ''">{{ r.estado_barrera || '—' }}</span></td>
            <td class="font-mono text-xs" :title="r.operacion_id || ''">{{ r.operacion_id || '—' }}</td>
            <td>{{ r.lista || '—' }}</td><td>{{ r.operador }}</td>
            <td>{{ r.origen }}</td><td class="max-w-64 truncate" :title="r.motivo">{{ r.motivo || '' }}</td>
          </tr>
          <tr v-if="!rows.length && !loading"><td colspan="14" class="py-6 text-center text-muted">Sin operaciones para estos filtros.</td></tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
