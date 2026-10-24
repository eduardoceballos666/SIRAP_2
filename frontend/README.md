# SIRAP · Frontend (Vue 3)

Vue 3 + Vite + Pinia + Vue Router + Tailwind CSS 4 · gráficos con ECharts.

```bash
npm install
npm run dev        # http://localhost:5173 (reenvía /api a http://localhost:8000)
npm run build      # genera dist/, que FastAPI sirve en http://localhost:8000
```

| Carpeta | Contenido |
|---|---|
| `src/views/` | Login, Reconocimiento y Acceso, Dashboard, Historial, Administración, Acerca del modelo |
| `src/components/` | Tarjeta de resultado, visor con la caja de la placa (SVG), íconos, logo, modal, avisos |
| `src/stores/` | Pinia: `auth` (token JWT y rol) y `session` (garita, movimiento, avisos) |
| `src/router/` | Rutas protegidas por sesión y por rol |
| `src/lib/` | Cliente HTTP (`api.js`), formatos y configuración de gráficos |
