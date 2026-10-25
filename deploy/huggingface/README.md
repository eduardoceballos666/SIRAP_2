---
title: SIRAP
emoji: 🚧
colorFrom: yellow
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Reconocimiento de placas y control de acceso (YOLO11 + OCR)
---

# SIRAP · Sistema de Detección y Reconocimiento Automático de Placas

Versión web (API FastAPI + interfaz Vue 3). Código fuente y documentación:
https://github.com/eduardoceballos666/SIRAP_2

Usuarios de demostración: `operador`, `supervisor` y `admin`. Los registros de demostración contienen **datos ficticios** y la
barrera es **simulada**. Este Space se actualiza automáticamente desde GitHub en cada cambio de la rama `main`.

## Guardado de detecciones en GitHub

La API agrega al CSV las operaciones confirmadas desde una detección. Después consulta el SRI y EcuadorLegalOnline en segundo plano y actualiza esa misma fila.

Configure estos valores en **Settings → Secrets and variables** del Space:

- `GITHUB_TOKEN`: token fine-grained limitado al repositorio de datos, con **Contents: Read and write**.
- `GITHUB_DATA_REPOSITORY`: `propietario/repositorio` de datos. Debe ser privado; la API rechaza repositorios públicos.
- `GITHUB_DATA_BRANCH`: rama destino (por defecto `main`).
- `GITHUB_DATA_PATH`: ruta CSV (por defecto `data/detecciones.csv`).

El archivo se crea con el encabezado si todavía no existe. El repositorio público del código puede seguir separado del repositorio privado de datos. La consulta a EcuadorLegalOnline guarda únicamente el nombre visible y su estado; si el sitio exige CAPTCHA o bloquea la consulta, se registra el estado y no se intenta eludir la restricción.
