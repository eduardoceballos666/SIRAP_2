import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

test('las aperturas limpian la lectura después de tres segundos sin depender de un clic DOM', async () => {
  const source = await readFile(new URL('../src/views/RecognitionView.vue', import.meta.url), 'utf8')
  const register = source.match(/async function register\(accion\) \{([\s\S]*?)\n\}\n\nfunction exportLecturas/)
  assert.ok(register, 'Debe existir la operación de registro de acceso')

  assert.match(
    register[1],
    /if \(\['APERTURA_MANUAL', 'APERTURA_AUTOMATICA'\]\.includes\(out\.accion\)\)/,
    'La limpieza automática solo se aplica tras aperturas registradas con éxito',
  )
  assert.match(
    register[1],
    /await nextTick\(\)[\s\S]*?await new Promise\(\(resolve\) => setTimeout\(resolve, 3000\)\)[\s\S]*?busy\.value = false\s*\n\s*clearCurrentReading\(\)/,
    'Tras mostrar el mensaje y esperar 3 segundos, debe liberarse busy y llamar a la limpieza directamente',
  )
  assert.doesNotMatch(register[1], /\.click\(\)/, 'No simular clic sobre un botón que podría seguir deshabilitado')

  assert.match(source, /@click="clearCurrentReading"/, 'Conservar el botón de limpieza manual')
  assert.doesNotMatch(source, /clearReadingButton/, 'Eliminar la referencia DOM innecesaria')
})
