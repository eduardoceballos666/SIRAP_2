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

La aplicación usa un umbral de confianza OCR de **94 %**, según [`config/config.yaml`](../config/config.yaml). Las lecturas por debajo pasan a verificación manual. En video o cámara continua, la misma placa debe alcanzar el umbral en dos cuadros aceptados dentro de 7,5 segundos; las lecturas inciertas requieren revisión humana.


## Aplicación y repositorio

La versión desplegada de la interfaz se encuentra en [SIRAP en Hugging Face](https://huggingface.co/spaces/eduardoceballos/SIRAP) y en https://eduardoceballos-sirap.hf.space. El [repositorio SIRAP_2](https://github.com/eduardoceballos666/SIRAP_2) contiene el frontend, la API y la configuración del despliegue. Consulta la [API interactiva](https://eduardoceballos-sirap.hf.space/docs), el [manual](../docs/manual_usuario.md) y los videos del [README principal](../README.md).