<script setup>
import { computed } from 'vue'
import AppIcon from '@/components/AppIcon.vue'

const props = defineProps({ decision: Object, loading: Boolean })
const STYLE = {
  AUTORIZADO: { box: 'border-ok bg-ok-soft', circle: 'bg-ok-dark', text: 'text-ok-dark', icon: 'check', title: 'ACCESO AUTORIZADO' },
  DENEGADO: { box: 'border-bad bg-bad-soft', circle: 'bg-bad', text: 'text-bad', icon: 'x', title: 'ACCESO DENEGADO' },
  NO_REGISTRADO: { box: 'border-warn bg-warn-soft', circle: 'bg-warn', text: 'text-warn', icon: 'alert', title: 'NO REGISTRADO' },
  VERIFICACION_MANUAL: { box: 'border-warn bg-warn-soft', circle: 'bg-warn', text: 'text-warn', icon: 'alert', title: 'VERIFICACIÓN MANUAL' },
}
const s = computed(() => STYLE[props.decision?.resultado])
</script>

<template>
  <div class="rounded-2xl border-4 p-5 transition" :class="s ? s.box : 'border-slate-200 bg-white'">
    <div class="flex items-center gap-4">
      <div class="grid h-20 w-20 shrink-0 place-items-center rounded-full text-white" :class="s ? s.circle : 'bg-slate-300'">
        <AppIcon v-if="s" :name="s.icon" :size="44" :stroke="3.2" />
        <span v-else-if="loading" class="h-9 w-9 animate-spin rounded-full border-4 border-white border-t-transparent"></span>
        <AppIcon v-else name="scan" :size="40" />
      </div>
      <div class="min-w-0">
        <p class="text-sm font-semibold tracking-wide">RESULTADO DE ACCESO</p>
        <p class="text-2xl leading-tight font-black sm:text-3xl" :class="s ? 'text-ink' : 'text-slate-400'">
          {{ s ? s.title : loading ? 'PROCESANDO…' : 'EN ESPERA' }}
        </p>
        <p class="text-lg font-bold" :class="s ? s.text : 'text-slate-400'">
          {{ decision ? decision.detalle : 'Seleccione o capture una imagen' }}
        </p>
      </div>
    </div>
    <ul v-if="decision?.motivos?.length" class="mt-3 list-disc space-y-0.5 pl-6 text-sm text-ink/80">
      <li v-for="m in decision.motivos" :key="m">{{ m }}</li>
    </ul>
    <p v-if="decision?.sugerencia" class="mt-2 text-sm font-semibold text-ink/80">
      ¿Quiso decir <span class="rounded bg-white px-1.5 py-0.5 font-mono">{{ decision.sugerencia }}</span>? (placa registrada parecida)
    </p>
  </div>
</template>
