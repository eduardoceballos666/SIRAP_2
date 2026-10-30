<script setup>
defineProps({ open: Boolean, title: String })
const emit = defineEmits(['close'])
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-40 grid place-items-center bg-navy-950/60 p-4" @click.self="emit('close')">
      <div class="w-full max-w-lg rounded-2xl bg-surface p-6 shadow-2xl" role="dialog" aria-modal="true">
        <h2 class="mb-4 text-xl font-bold">{{ $t(title) }}</h2>
        <slot />
      </div>
    </div>
  </Teleport>
</template>
