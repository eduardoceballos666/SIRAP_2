import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

test('registro de camiones exige revisión visual y autorización expresa', async () => {
  const src = await readFile(new URL('../src/views/RecognitionView.vue', import.meta.url), 'utf8')
  assert.match(src, /const plateConfirmedForRegistration = ref\(false\)/)
  assert.match(src, /const authorizeOnRegistration = ref\(false\)/)
  assert.match(src, /placa_confirmada: plateConfirmedForRegistration\.value/)
  assert.match(src, /autorizar: authorizeOnRegistration\.value/)
  assert.match(src, /!plateConfirmedForRegistration/)
  assert.match(src, /v-model="plateConfirmedForRegistration"/)
  assert.match(src, /v-model="authorizeOnRegistration"/)
  assert.doesNotMatch(src, /Puede continuar con la autorización automática/)
})

test('operaciones llevan UUID persistente durante reintentos de la misma lectura', async () => {
  const src = await readFile(new URL('../src/views/RecognitionView.vue', import.meta.url), 'utf8')
  assert.match(src, /const operationAttemptId = ref\(null\)/)
  assert.match(src, /if \(!operationAttemptId\.value\) operationAttemptId\.value = crypto\.randomUUID\(\)/)
  assert.match(src, /operacion_id: operationAttemptId\.value/)
  assert.match(src, /operationAttemptId\.value = null/)
})
