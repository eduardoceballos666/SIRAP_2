<script setup>
import { useSessionStore } from '@/stores/session'
const session = useSessionStore()
const tone = { ok: 'bg-ok-dark', bad: 'bg-bad', warn: 'bg-warn' }
</script>

<template>
  <div class="pointer-events-none fixed right-4 bottom-4 z-50 flex w-[min(92vw,380px)] flex-col gap-2" aria-live="polite">
    <TransitionGroup enter-from-class="translate-y-2 opacity-0" leave-to-class="opacity-0" enter-active-class="transition" leave-active-class="transition">
      <div v-for="t in session.toasts" :key="t.id" :class="tone[t.kind] || tone.ok"
           class="pointer-events-auto rounded-xl px-4 py-3 text-sm font-semibold text-white shadow-lg">{{ $t(t.message) }}</div>
    </TransitionGroup>
  </div>
</template>
