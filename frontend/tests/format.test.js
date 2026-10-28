import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

import { ACTION, RESULT, TONE_PILL, num, pct } from '../src/lib/format.js'

test('format helpers handle confidence values and missing values', () => {
  assert.equal(pct(0.985, 1), '98.5%')
  assert.equal(pct(null), '—')
  assert.equal(num(0.12345, 2), '0.12')
  assert.equal(num(undefined), '—')
})

test('access results expose labels and styles used by the Vue views', () => {
  assert.equal(RESULT.AUTORIZADO.label, 'Autorizado')
  assert.equal(RESULT.DENEGADO.tone, 'bad')
  assert.equal(TONE_PILL.ok, 'bg-ok-soft text-ok-dark')
  assert.equal(ACTION.APERTURA_MANUAL, 'Apertura manual')
})

test('history view keeps CSV export available to authorized roles', async () => {
  const source = await readFile(new URL('../src/views/HistoryView.vue', import.meta.url), 'utf8')
  assert.match(source, /Exportar CSV/)
  assert.match(source, /\/api\/operations\/export\.csv/)
  assert.match(source, /auth\.hasRole\('SUPERVISOR', 'ADMINISTRADOR'\)/)
})
