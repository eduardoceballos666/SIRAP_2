export const RESULT = {
  AUTORIZADO: { label: 'Autorizado', title: 'ACCESO AUTORIZADO', tone: 'ok' },
  DENEGADO: { label: 'Denegado', title: 'ACCESO DENEGADO', tone: 'bad' },
  NO_REGISTRADO: { label: 'No registrado', title: 'NO REGISTRADO', tone: 'warn' },
  VERIFICACION_MANUAL: { label: 'Verificación manual', title: 'VERIFICACIÓN MANUAL', tone: 'warn' },
}
export const ACTION = {
  APERTURA_AUTOMATICA: 'Apertura automática',
  APERTURA_MANUAL: 'Apertura manual',
  SOLO_REGISTRO: 'Solo registro',
  RECHAZO: 'Rechazo',
}
export const TONE_PILL = {
  ok: 'bg-ok-soft text-ok-dark',
  bad: 'bg-bad-soft text-bad',
  warn: 'bg-warn-soft text-warn',
}
export const pct = (v, d = 0) => (v === null || v === undefined ? '—' : `${(v * 100).toFixed(d)}%`)
export const num = (v, d = 3) => (v === null || v === undefined ? '—' : Number(v).toFixed(d))
export function today(offsetDays = 0) {
  const d = new Date(); d.setDate(d.getDate() + offsetDays)
  return d.toLocaleDateString('en-CA') // AAAA-MM-DD en hora local
}
export function formatDateTime(value, locale = 'es-EC') {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString(locale)
}
