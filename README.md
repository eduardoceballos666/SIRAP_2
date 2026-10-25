<div align="center">

# 🚧 SIRAP 2
### Sistema de Detección y Reconocimiento Automático de Placas · versión web FastAPI + Vue 3

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/API-FastAPI%200.162-009688?logo=fastapi&logoColor=white)
![Vue](https://img.shields.io/badge/Frontend-Vue%203.5-42b883?logo=vuedotjs&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind%20CSS-4-06b6d4?logo=tailwindcss&logoColor=white)
![YOLO11](https://img.shields.io/badge/Detector-YOLO11--s-0b2a6b)
![OCR](https://img.shields.io/badge/OCR-fast--plate--ocr-2156e8)
![Tests](https://img.shields.io/badge/tests-pytest-0f8a3c)
![Deploy](https://img.shields.io/badge/Hugging%20Face-Space-ffcc4d?logo=huggingface&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-yellow)

**SIRAP** reconoce la placa del vehículo que llega a una garita, la busca en el registro CSV y propone una
decisión de acceso (autorizado, denegado, no registrado o verificación manual). El operador confirma, la operación
queda registrada y la barrera se abre solo cuando corresponde. **SIRAP 2** ofrece el mismo sistema como una
aplicación web profesional: **API REST en FastAPI** con autenticación por usuario y **frontend en Vue 3**.

[**Aplicación en vivo**](https://eduardoceballos-sirap.hf.space) · [Manual de usuario](docs/manual_usuario.md) ·
[Documentación de la API](https://eduardoceballos-sirap.hf.space/docs) · [Notebook de backend](notebooks/SIRAP_backend.ipynb)

<img src="docs/img/vue_reconocimiento.png" alt="SIRAP 2 – Reconocimiento y Acceso" width="900">

</div>

---

## Tabla de contenidos

1. [Problema](#1-problema)
2. [Dataset](#2-dataset)
3. [Metodología](#3-metodología)
4. [Resultados](#4-resultados)
5. [Instalación y uso](#5-instalación-y-uso)
6. [Interfaz de usuario](#6-interfaz-de-usuario)
7. [Estructura del proyecto](#7-estructura-del-proyecto)
8. [Consideraciones éticas](#8-consideraciones-éticas)
9. [Autores](#9-autores-y-contribuciones)
10. [Licencia](#10-licencia)
11. [Agradecimientos y referencias](#11-agradecimientos-y-referencias)
12. [Videos](#12-videos)

## 1. Problema

En urbanizaciones, edificios, empresas, plantas y estacionamientos el control vehicular de la garita es manual: el
guardia lee la placa, la busca en una lista y la anota. Eso produce **colas**, **errores de transcripción**,
**listas desactualizadas** y un historial difícil de auditar.

**SIRAP** automatiza el flujo: **captura → detección de la placa (IA) → lectura (OCR) → consulta en la base
(CSV locales) → evaluación de listas blancas y restringidas → registro y apertura controlada**.

- **Por qué importa:** menos espera, menos errores, seguridad basada en listas vigentes y trazabilidad completa.
- **Usuarios:** operadores de garita (deciden y registran), supervisores (auditan) y administradores (gestionan
  vehículos, listas, garitas y usuarios).

## 2. Dataset

| Dataset | Uso | Tamaño | Licencia / fuente |
|---|---|---|---|
| [License Plate Recognition v11](https://universe.roboflow.com/roboflow-universe-projects/license-plate-recognition-rxg4e) (Roboflow Universe) | Entrenar y evaluar el detector | 10 125 imágenes (7 057 / 2 048 / 1 020), 1 clase, 10 637 placas | CC BY 4.0 |
| SAVH Guayaquil ANPR Plate Images | Evaluar el OCR con placas **ecuatorianas** reales | 739 recortes (472 legibles; 399 legibles únicas) | Zenodo (público) |
| Video e imágenes de la garita | Pipeline de video y prueba punta a punta | 1 video de 10 min (18 115 cuadros) | Propio, con autorización escrita; **no se publica** |

Detalles, EDA y decisiones de preprocesamiento: [`docs/analisis_datos.md`](docs/analisis_datos.md) y
[`data/README.md`](data/README.md).

## 3. Metodología

| Etapa | Elección | Justificación |
|---|---|---|
| Detección | **YOLO11-s** (Ultralytics 8.4.177), 9,41 M parámetros | Una sola clase; rápido; se exporta a ONNX y corre en CPU en la app |
| Seguimiento (video) | OC-SORT | Leer cada vehículo una sola vez, con su mejor recorte |
| OCR | **fast-plate-ocr** `cct-s-v2-global-model` (5 MB) | Hecho para placas, 16 ms por recorte en CPU, 93,7 % de EMR en placas reales de Guayaquil |
| Normalización | Formato `XXX-0000`, correcciones letra/dígito por posición (máx. 2) | Validada con placas reales de Guayaquil |
| Decisión | Listas blanca/restringida + umbrales + «¿quiso decir…?» | Nunca decide a ciegas: lo dudoso va a verificación manual |
| Datos | SQLite local de demostración | Vehículos, propietarios, listas, garitas, usuarios e historial |

**Preprocesamiento:** copia local del dataset, `data.yaml` con rutas absolutas, *letterbox* a 640 px, aumentos por
defecto de Ultralytics; recorte con margen antes del OCR.
**Entrenamiento:** `yolo11s.pt` (COCO) → 40 épocas, imgsz 640, batch 16 (nbs 64), paciencia 10, semilla 0, AdamW.
**Optimización:** calibración de umbrales en *val* (detector: precisión ≥ 95 %; OCR: estudio de confianza en SAVH),
resolución de inferencia en video (640 → 1280 px) y estudio de sensibilidad de hiperparámetros (Optuna + fANOVA +
PDP, 24 *trials*) en [`notebooks/04_optimizacion.ipynb`](notebooks/04_optimizacion.ipynb): `lr0` explica el 62 % de
la variación del mAP; la mejor configuración (`lr0` ≈ 1,6e-4) sube el mAP@0.5:0.95 de *test* de 0,693 a 0,704 con el
mismo mAP@0.5, y se mantiene el modelo entregado — ver [`docs/optimizacion.md`](docs/optimizacion.md).
**Métricas:** mAP@0.5 y mAP@0.5:0.95 (también por tamaño de placa), precisión, recall y F1 al umbral calibrado;
EMR y CER para el OCR; falsos autorizados y tiempo por decisión para el sistema.

Arquitectura completa y diagramas: [`docs/arquitectura.md`](docs/arquitectura.md).

## 4. Resultados

Preset «completo», split *test* nunca visto en el entrenamiento (salidas del notebook, `results/metrics/`).

| Componente | Métrica | Resultado | Meta |
|---|---|---|---|
| Detector YOLO11-s | mAP@0.5 | **0,972** | ≥ 0,85 ✅ |
| | mAP@0.5:0.95 | 0,693 | — |
| | Precisión / Recall / F1 (umbral 0,30) | 0,986 / 0,956 / 0,971 | — |
| | mAP@0.5:0.95 placas pequeñas / medianas / grandes | 0,481 / 0,729 / 0,744 | — |
| | Latencia (lote 1, FP16, GPU L4) | 23,3 ms (43 FPS) | — |
| Detector con hiperparámetros optimizados (Optuna, 24 *trials*) | mAP@0.5 / mAP@0.5:0.95 *test* | 0,973 / 0,704 (+0,011, una semilla): se mantiene el entregado | — |
| OCR (SAVH Guayaquil, 399 legibles) | EMR / CER | **93,7 %** / 0,010 | EMR ≥ 80 % ✅ |
| OCR afinado con placas ecuatorianas (*test* separado por placa, n=86) | EMR original / afinado | 94,2 % / 94,2 % (McNemar *p* = 1,0): se mantiene el original | — |
| Regla de decisión (SAVH, lista simulada) | Falsos autorizados / rechazos indebidos | 0 de 202 / 1 de 197 | — |
| Sistema (video de la garita) | Tiempo por decisión (detección + OCR) | 99 ms | ≤ 1 s ✅ |
| Sistema | EMR punta a punta | pendiente (requiere referencia anotada del video) | ≥ 80 % |

**Comparación con un *baseline*.** El primer entrenamiento (época 1, equivalente a usar el modelo apenas
adaptado) logra mAP@0.5 = 0,848 en *val*; el modelo final llega a 0,971 (+0,12). En el OCR, el *baseline* es el
mismo fast-plate-ocr sin la normalización ecuatoriana: solo con limpieza de texto logra 93,5 % de EMR en SAVH y con
`normalize_plate` 93,7 %, con todas las lecturas en formato válido; afinarlo con placas ecuatorianas no lo mejoró
(94,2 % frente a 94,2 % en un *test* separado por placa, McNemar *p* = 1,0).

<img src="results/figures/resumen_yolo11_completo.png" alt="Resultados de YOLO11-s" width="900">

**Dónde funciona bien y dónde no:** muy bien con placas medianas y grandes de frente y de día; peor con placas
pequeñas (lejanas), de noche o deterioradas. Por eso el video se analiza a 1280 px y las lecturas dudosas van a
verificación manual.

## 5. Instalación y uso

**Requisitos:** Python 3.11+, Node.js 20.19+ (solo para compilar el frontend), 2 GB de RAM; GPU solo para entrenar
(Colab). Alternativa sin instalar nada: Docker.

```bash
git clone https://github.com/eduardoceballos666/SIRAP_2.git
cd SIRAP_2
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # defina SIRAP_JWT_SECRET (cadena larga y aleatoria)

cd frontend && npm ci && npm run build && cd ..        # compila la interfaz Vue en frontend/dist
uvicorn api.main:app --port 8000                       # abre http://localhost:8000 (API + interfaz)
```

Usuarios de demostración: `operador`, `supervisor` y `admin`; contraseña `sirap2026` (se cambia con
`SIRAP_DEMO_PASSWORD`).

| Tarea | Comando |
|---|---|
| Desarrollo con recarga en caliente | `uvicorn api.main:app --reload` y, en otra terminal, `cd frontend && npm run dev` (http://localhost:5173) |
| Docker (API + interfaz) | `docker build -t sirap2 . && docker run -p 7860:7860 -e SIRAP_JWT_SECRET=... sirap2` → http://localhost:7860 |
| Documentación interactiva de la API | http://localhost:8000/docs (Swagger) |
| Pruebas (unitarias, integración y API) | `pip install -r requirements-dev.txt && pytest` |
| Interfaz alternativa en Streamlit | `streamlit run app.py` → http://localhost:8501 |
| Exportar los pesos entrenados a ONNX | `python -m src.train --export-only models/best_model.pt` |
| Reentrenar (no hace falta) | `ROBOFLOW_API_KEY=... python -m src.train --roboflow --force` |
| Evaluar el detector en *test* | `python -m src.evaluate detector --data <data.yaml>` |

**Configuración:** parámetros en [`config/config.yaml`](config/config.yaml); secretos en variables de entorno
(plantillas [`.env.example`](.env.example) y [`api/.env.example`](api/.env.example)): `SIRAP_JWT_SECRET`,
`SIRAP_DEMO_PASSWORD`, `BARRERA_URL`, `BARRERA_TOKEN`, `ROBOFLOW_API_KEY`. La API conserva datos de demostración en un archivo local temporal; las lecturas del notebook se guardan como CSV.

**Ejemplo de uso de la API:**

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/auth/login -H 'Content-Type: application/json' \
        -d '{"usuario":"operador","password":"sirap2026"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
curl -s -X POST localhost:8000/api/recognize -H "Authorization: Bearer $TOKEN" \
     -F file=@data/samples/garita3_PBA-8901.jpg
# {"recognition": {"plate": "PBA-8901", "ocr_confidence": 0.9999, ...}, "decision": {"resultado": "AUTORIZADO", ...}}
```

**Desde Python:**

```python
from src.model import ALPRPipeline
from src.database import Database
from src.access_control import decide_access
from src.data_processing import load_image

pipeline, db = ALPRPipeline.from_config(), Database.from_environment()
rec = pipeline.recognize(load_image(open("data/samples/garita3_PBA-8901.jpg", "rb").read()))
print(rec.plate, f"{rec.ocr_confidence:.2%}")                       # PBA-8901 99.99%
print(decide_access(rec.plate, rec.ocr_confidence, db).titulo)      # ACCESO AUTORIZADO
```

## 6. Interfaz de usuario

**Opción D del enunciado: FastAPI + frontend Vue 3** (Vite, Pinia, Vue Router, Tailwind CSS, ECharts), con el diseño
de la guía [`docs/img/SIRAP_Dashboard.png`](docs/img/SIRAP_Dashboard.png). Publicada en
**https://eduardoceballos-sirap.hf.space** (Hugging Face Spaces). Guía completa: [manual de usuario](docs/manual_usuario.md).

| Módulo | Qué hace |
|---|---|
| **Inicio de sesión** | Usuario y contraseña; cada operación queda firmada por el usuario y su rol (operador, supervisor, administrador) |
| **Reconocimiento y Acceso** | Botones «Probar con un ejemplo», subir foto o cámara → caja de la placa sobre la imagen, placa, confianza OCR, recorte, resultado de acceso y datos del vehículo; registrar y abrir, reprocesar, apertura manual con motivo, registrar rechazo; corrección manual de la placa; **lecturas de la sesión** para comparar y exportar a CSV; ayuda «¿Cómo se usa esta pantalla?» |
| **Dashboard** | Ingresos, salidas, placas identificadas y alertas; gráficos interactivos (ECharts) por hora, resultado y garita |
| **Historial** | Filtros por fecha, placa, garita, resultado y movimiento; exportación CSV (supervisor y administrador) |
| **Administración** | Vehículos, listas blanca/restringida con vigencia, propietarios, garitas, usuarios con contraseña; datos de demostración |
| **Acerca del modelo** | Funcionamiento, métricas, entrenamiento, optimización y **limitaciones y advertencias** |

**Requisitos de la interfaz cubiertos:** validación de entradas (tipo, tamaño y resolución de imagen en el servidor;
formato de placa), indicador de carga, mensajes de error comprensibles (sin trazas técnicas), confianza OCR y de
detección, visualizaciones (caja sobre la imagen, recorte, gráficos), ejemplos precargados, diseño adaptable a
celular, **tema claro/oscuro** (botón sol/luna), historial y comparación de las lecturas de la sesión y exportación CSV.

| Reconocimiento (anotado en el manual) | Dashboard | Tema oscuro | Celular |
|---|---|---|---|
| <img src="docs/img/vue_reconocimiento.png" width="300"> | <img src="docs/img/vue_dashboard.png" width="300"> | <img src="docs/img/vue_verificacion.png" width="300"> | <img src="docs/img/vue_movil.png" width="110"> |

### 6.1 API REST

Documentación interactiva (Swagger) en [`/docs`](https://eduardoceballos-sirap.hf.space/docs).

| Endpoint | Rol | Uso |
|---|---|---|
| `POST /api/auth/login` · `GET /api/auth/me` | — | Inicio de sesión (JWT con rol, 12 h) |
| `POST /api/recognize` | todos | Imagen → placa, confianza, caja, recorte y decisión (no registra) |
| `POST /api/plates/verify` | todos | Verificar una placa escrita o corregida a mano |
| `POST /api/operations` | todos | Registrar la operación; el servidor recalcula la decisión, solo abre automáticamente si está AUTORIZADO y exige motivo en la apertura manual |
| `GET /api/operations` · `/api/operations/export.csv` | todos · supervisor/admin | Historial filtrado y exportación CSV |
| `GET /api/dashboard` | todos | Indicadores y datos de los gráficos |
| `GET/POST/DELETE /api/admin/...` | admin (lectura: supervisor) | Vehículos, listas, garitas, usuarios, datos de demostración |
| `GET /api/system` · `/api/model/info` · `/api/samples` | todos | Estado, métricas del modelo e imágenes de ejemplo |

### 6.2 Despliegue

El workflow [`.github/workflows/deploy-hf-space.yml`](.github/workflows/deploy-hf-space.yml) publica la app en el
Space `eduardoceballos/sirap` en cada push a `main` (o a mano desde *Actions → Run workflow*); Hugging Face construye
el [`Dockerfile`](Dockerfile) (frontend compilado + API, puerto 7860). Configuración, una sola vez, en GitHub →
*Settings → Secrets and variables → Actions*:

| Nombre | Tipo | Valor |
|---|---|---|
| `HF_TOKEN` | Secret (obligatorio) | Token de Hugging Face con permiso **Write** |
| `SIRAP_JWT_SECRET` | Secret (recomendado) | Cadena larga y aleatoria para firmar las sesiones |
| `SIRAP_DEMO_PASSWORD` | Secret (opcional) | Contraseña de los usuarios de demostración |
| `HF_SPACE` | Variable (opcional) | Otro Space, p. ej. `usuario/sirap` |

El Space usa el hardware *CPU basic* (en cuentas nuevas de Hugging Face requiere PRO). La API ocupa ≈410 MB de RAM
con los modelos cargados, por eso no se recomiendan planes gratuitos de 512 MB (Render, Railway).

> **Interfaz alternativa.** El repositorio conserva la app de **Streamlit** (`app/`, `streamlit run app.py`), que usa
> el mismo backend. Su versión publicada vive en el repositorio original
> [SIRAP](https://github.com/eduardoceballos666/SIRAP) (https://sirapapp.streamlit.app/).

> **Estado:** prototipo funcional. La barrera es **simulada** y la base pública contiene **datos ficticios** que se
> reinician con el servidor. Para operar en una garita real faltan: la cámara IP, la cámara IP y el controlador de la
> barrera.

## 7. Estructura del proyecto

```
SIRAP_2/
├── api/                    # API REST FastAPI: main.py, routers/ (auth, recognition, reports, admin), security.py (JWT + PBKDF2), schemas.py
├── frontend/               # interfaz Vue 3: src/views, src/components, src/stores (Pinia), src/router, src/lib
├── src/                    # backend: data_processing, model, access_control, storage, train, evaluate, utils
├── app/                    # interfaz alternativa en Streamlit: app.py, ui.py, assets/style.css, requirements.txt
├── app.py                  # punto de entrada de Streamlit (ejecuta app/app.py)
├── notebooks/              # SIRAP_backend.ipynb (completo) y 01–06 (EDA, preprocesamiento, modelado, optimización, evaluación, OCR)
├── models/                 # pesos de YOLO11-s (best_model.pt / .onnx) y ficha del modelo
├── data/                   # samples/ (ejemplos de la app), raw/, processed/ y descripción de los datos
├── data/processed/         # CSV de vehículos, listas, usuarios e historial
├── config/config.yaml      # parámetros (sin secretos)
├── docs/                   # planificación, EDA, arquitectura, optimización, ética, manual e imágenes
├── results/                # figures/, metrics/ (JSON/CSV del notebook), reports/
├── tests/                  # pytest: procesamiento, modelo, decisión, base de datos, app y API
├── deploy/huggingface/     # README del Space y script de publicación
├── .github/workflows/      # despliegue automático en Hugging Face Spaces
├── Dockerfile              # imagen única: frontend compilado + API
├── requirements.txt        # dependencias con versiones (backend, API y Streamlit)
└── requirements-dev.txt    # entrenamiento, notebooks y pruebas
```

## 8. Consideraciones éticas

Resumen de [`docs/consideraciones_eticas.md`](docs/consideraciones_eticas.md):

- **Privacidad:** una placa identifica indirectamente a una persona. No se guardan imágenes; datos mínimos de
  propietarios; demo con datos ficticios; secretos fuera del código; marco de la LOPDP de Ecuador (letrero
  informativo, plazo de conservación, derechos de los titulares).
- **Sesgos:** detector entrenado con placas de otros países; OCR validado solo en Guayaquil; peor desempeño con
  placas pequeñas (mAP 0,481), nocturnas o deterioradas.
- **Mitigación:** umbrales calibrados, verificación manual de todo lo dudoso, corrección manual, la barrera nunca se
  abre sola, apertura de contingencia con motivo y auditoría de solo inserción.
- **Responsabilidad:** cada operación queda asociada al usuario autenticado y su rol; el servidor vuelve a calcular la
  decisión antes de registrar, de modo que la interfaz no puede forzar una apertura automática.
- **Uso indebido:** no usar para vigilancia masiva, seguimiento de personas, multas o decisiones sin operador.

## 9. Autores y contribuciones

| Integrante | Rol |
|---|---|
| **Eduardo Alejandro Ceballos Jijón** | Modelado y entrenamiento de YOLO11-s y OCR (fast-plate-ocr) |
| **Christian Xavier Valle Maridueña** | Datos (SAVH Guayaquil e imágenes de la garita) y desarrollo de la interfaz web Vue 3 |

*Maestría en Inteligencia Artificial — Proyecto Integrador en IA (MIAR0545), 2026.*

## 10. Licencia

Código bajo licencia [MIT](LICENSE). Los pesos entrenados con Ultralytics están sujetos a su licencia AGPL-3.0;
el dataset de Roboflow es CC BY 4.0.

## 11. Agradecimientos y referencias

- Ultralytics YOLO11 — https://docs.ultralytics.com/models/yolo11/
- fast-plate-ocr — https://github.com/ankandrew/fast-plate-ocr
- OC-SORT / `trackers` y `supervision` de Roboflow — https://github.com/roboflow/trackers
- Roboflow Universe, *License Plate Recognition* — https://universe.roboflow.com/roboflow-universe-projects/license-plate-recognition-rxg4e
- SAVH Guayaquil ANPR Plate Images Dataset — Zenodo
- FastAPI — https://fastapi.tiangolo.com/ · Vue 3 — https://vuejs.org/ · Vite — https://vite.dev/ · Pinia —
  https://pinia.vuejs.org/ · Vue Router — https://router.vuejs.org/ · Tailwind CSS — https://tailwindcss.com/ ·
  Apache ECharts — https://echarts.apache.org/
- Streamlit — https://streamlit.io/ · Plotly — https://plotly.com/python/ · Hugging Face Spaces — https://huggingface.co/spaces
- A la empresa que autorizó la toma de imágenes en su garita, y a los docentes del programa.

## 12. Videos

- 🎬 **Video pitch (5 min):** _pendiente de grabación y publicación_
- 🎤 **Video de respuestas a las preguntas:** _pendiente de grabación y publicación_
