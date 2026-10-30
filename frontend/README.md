# SIRAP · Frontend (Vue 3)

Vue 3 + Vite + Pinia + Vue Router + Tailwind CSS 4 · gráficos con ECharts · tema claro/oscuro (variables CSS en `src/style.css`).

```bash
npm install
npm run dev        # http://localhost:5173 (reenvía /api a http://localhost:8000)
npm run build      # genera dist/, que FastAPI sirve en http://localhost:8000
```

| Carpeta | Contenido |
|---|---|
| `src/views/` | Login, Reconocimiento y Acceso, Dashboard, Historial, Administración, Acerca del modelo |
| `src/components/` | Tarjeta de resultado, visor con la caja de la placa (SVG), íconos, logo, modal, avisos |
| `src/stores/` | Pinia: `auth` (token JWT y rol) y `session` (garita, movimiento, tema claro/oscuro, avisos y lecturas de la sesión) |
| `src/router/` | Rutas protegidas por sesión y por rol |
| `src/lib/` | Cliente HTTP (`api.js`), formatos y configuración de gráficos |

## Idiomas de la interfaz

El frontend ofrece **Español** (predeterminado) e **English**. Se accede a ambos desde la misma aplicación publicada: https://eduardoceballos-sirap.hf.space. El selector **Idioma** aparece en el inicio de sesión y en el menú compartido tras iniciar sesión; la elección se conserva en `localStorage` (`sirap_language`) al navegar y reabrir la app en el mismo navegador. Las cadenas de interfaz se mantienen en el catálogo central `src/i18n.js`; las vistas deben usar `$t()` en textos visibles y mensajes para que respeten el idioma seleccionado.

## Umbral operativo OCR

La aplicación usa un umbral de confianza OCR de **99 %**. Las lecturas por debajo pasan a verificación manual.
