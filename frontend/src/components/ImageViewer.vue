<script setup>
import { computed } from 'vue'
import AppIcon from '@/components/AppIcon.vue'

// Muestra la imagen y dibuja la caja de la placa como SVG escalable (sin re-codificar la imagen).
const props = defineProps({ src: String, box: Array, width: Number, height: Number, tone: String, label: String,
  garita: String, stamp: String, loading: Boolean })
const color = computed(() => ({ ok: '#16dc3c', bad: '#ff2b33', warn: '#ffb000' }[props.tone] || '#16dc3c'))
const stroke = computed(() => Math.max(3, Math.round((props.width || 1000) / 220)))
const fontSize = computed(() => Math.max(16, Math.round((props.width || 1000) / 45)))
</script>

<template>
  <div class="relative overflow-hidden rounded-2xl bg-navy-900 p-2">
    <div v-if="src" class="relative">
      <img :src="src" alt="Imagen de la garita" class="block max-h-[62vh] w-full rounded-xl object-contain" />
      <svg v-if="box && width && height" :viewBox="`0 0 ${width} ${height}`" preserveAspectRatio="xMidYMid meet"
           class="pointer-events-none absolute inset-0 h-full w-full">
        <rect :x="box[0]" :y="box[1]" :width="box[2] - box[0]" :height="box[3] - box[1]" fill="none"
              :stroke="color" :stroke-width="stroke" rx="4" />
        <template v-if="label">
          <rect :x="box[0]" :y="Math.max(0, box[1] - fontSize * 1.5)" :width="label.length * fontSize * 0.68 + fontSize"
                :height="fontSize * 1.35" :fill="color" rx="4" />
          <text :x="box[0] + fontSize * 0.5" :y="Math.max(fontSize * 1.05, box[1] - fontSize * 0.42)" :font-size="fontSize"
                font-weight="800" fill="#0d1b33" font-family="Inter, Arial, sans-serif">{{ label }}</text>
        </template>
      </svg>
      <div v-if="loading" class="absolute inset-0 grid place-items-center rounded-xl bg-navy-950/45">
        <span class="h-12 w-12 animate-spin rounded-full border-4 border-white border-t-transparent"></span>
      </div>
      <span class="absolute bottom-3 left-3 flex items-center gap-2 rounded-lg bg-navy-950/75 px-3 py-1.5 text-sm text-white">
        <AppIcon name="camera" :size="16" /> {{ garita }}
      </span>
      <span v-if="stamp" class="absolute right-3 bottom-3 rounded-lg bg-navy-950/75 px-3 py-1.5 text-sm text-white">{{ stamp }}</span>
    </div>
    <div v-else class="grid aspect-video place-items-center rounded-xl border-2 border-dashed border-white/20 text-slate-300">
      <div class="text-center">
        <AppIcon name="image" :size="64" class="mx-auto mb-4 opacity-70" />
        <p class="text-3xl font-bold leading-tight">Sin imagen</p>
        <p class="mt-2 text-xl leading-relaxed opacity-90">Elija un ejemplo, suba una foto o use la cámara.</p>
      </div>
    </div>
  </div>
</template>
