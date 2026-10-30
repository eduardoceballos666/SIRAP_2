<script setup>
import { language, setLanguage } from '@/i18n'

function changeLanguage(event) {
  setLanguage(event.target.value)
}
</script>

<template>
  <label class="language-switcher">
    <span>{{ $t('Idioma') }}</span>
    <select :value="language" :aria-label="$t('Idioma')" @change="changeLanguage">
      <option value="es">Español</option>
      <option value="en">English</option>
    </select>
  </label>
</template>
