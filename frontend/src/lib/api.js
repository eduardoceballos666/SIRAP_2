// Cliente HTTP mínimo: agrega el token JWT y traduce los errores de FastAPI a mensajes legibles.
const TOKEN_KEY = 'sirap_token'

export function getToken() {
  try { return localStorage.getItem(TOKEN_KEY) } catch { return null }
}
export function setToken(token) {
  try { token ? localStorage.setItem(TOKEN_KEY, token) : localStorage.removeItem(TOKEN_KEY) } catch { /* sin almacenamiento */ }
}

export class ApiError extends Error {
  constructor(status, message) { super(message); this.status = status }
}

let onUnauthorized = () => {}
export function setUnauthorizedHandler(fn) { onUnauthorized = fn }

function detailMessage(body, status) {
  const d = body?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((e) => `${(e.loc || []).slice(1).join('.')}: ${e.msg}`).join(' · ')
  return `Error ${status}`
}

export async function api(path, { method = 'GET', body, form, params, raw = false } = {}) {
  const url = new URL(path, window.location.origin)
  Object.entries(params || {}).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v) })
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  let payload
  if (form) payload = form
  else if (body !== undefined) { headers['Content-Type'] = 'application/json'; payload = JSON.stringify(body) }
  let res
  try {
    res = await fetch(url, { method, headers, body: payload })
  } catch {
    throw new ApiError(0, 'No se pudo conectar con la API de SIRAP.')
  }
  if (res.status === 401 && token) onUnauthorized()
  if (!res.ok) {
    let data = null
    try { data = await res.json() } catch { /* cuerpo vacío */ }
    throw new ApiError(res.status, detailMessage(data, res.status))
  }
  if (raw) return res
  return res.status === 204 ? null : res.json()
}
