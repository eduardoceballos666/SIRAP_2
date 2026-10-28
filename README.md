<div align="center">

# SIRAP
### Sistema de Detección y Reconocimiento Automático de Placas · versión del producto 1.0 · FastAPI + Vue 3

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
decisión de acceso (autorizado, denegado, no registrado o verificación manual). El operador inicia el registro y solicita la apertura desde SIRAP. El servidor vuelve a validar la autorización: solo permite la apertura automática si el acceso está autorizado; la apertura manual de contingencia requiere un motivo. La aplicación ejecuta la orden solicitada y, en la demostración, la barrera es simulada. La versión 1.0 de **SIRAP** ofrece el sistema como una
aplicación web profesional: **API REST en FastAPI** con autenticación por usuario y **frontend en Vue 3**.

[**Aplicación en vivo**](https://eduardoceballos-sirap.hf.space) · [Manual de usuario](docs/manual_usuario.md) ·
[Documentación de la API](https://eduardoceballos-sirap.hf.space/docs) · [Notebook de backend](notebooks/SIRAP_backend.ipynb)

<img src="https://raw.githubusercontent.com/eduardoceballos666/SIRAP_2/396855f38f95c209d201768d6e31312dc7d41203/docs/img/vue_reconocimiento.png" alt="SIRAP – Reconocimiento y Acceso" width="900">

</div>

---

## Versiones del proyecto

- **Versión del producto SIRAP:** 1.0.
- **API:** 2.0.0, identificador técnico expuesto por FastAPI/OpenAPI y el endpoint de salud.
- **Frontend:** 2.0.0 es la versión del paquete npm en `frontend/package.json`; no es la versión del producto.
- **Tag de GitHub `v2.0`:** identifica el corte del repositorio publicado con la arquitectura FastAPI + Vue 3 (release titulada «SIRAP 2.0 – FastAPI + Vue 3»). Es un identificador técnico e histórico del código; el producto SIRAP continúa en la versión 1.0.

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
| [SAVH Guayaquil ANPR Plate Images](https://zenodo.org/records/21120307) | Evaluar el OCR con placas **ecuatorianas** reales | 739 recortes (472 legibles; 399 legibles únicas) | Zenodo; el registro no muestra licencia para este archivo específico |
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
| Datos | Archivos CSV locales | Vehículos, propietarios, listas, garitas, usuarios e historial |

**Preprocesamiento:** copia local del dataset, `data.yaml` con rutas absolutas, *letterbox* a 640 px, aumentos por
defecto de Ultralytics; recorte con margen antes del OCR.
**Entrenamiento:** `yolo11s.pt` (COCO) → 40 épocas, imgsz 640, batch 16 (nbs 64), paciencia 10, semilla 0, AdamW.
**Optimización:** los umbrales se calibraron en *val* (detector: precisión ≥ 95 %; OCR: estudio de confianza en SAVH); la inferencia de video se comparó a 640 y 1280 px. Los 24 *trials* de Optuna seleccionaron hiperparámetros según mAP@0.5:0.95 en *val*; `lr0` explicó el 62 % de la variación. El *test* se reservó para la comparación final del modelo base y el optimizado (1.020 imágenes, 1.085 placas): mAP@0.5:0.95 pasó de 0,693 a 0,704 (+0,011) y mAP@0.5 de 0,97223 a 0,97284 (+0,00061; redondeado a tres decimales: 0,972 y 0,973). Se mantiene el modelo entregado — ver [`notebooks/04_optimizacion.ipynb`](notebooks/04_optimizacion.ipynb) y [`docs/optimizacion.md`](docs/optimizacion.md).
**Métricas:** mAP@0.5 y mAP@0.5:0.95 (también por tamaño de placa), precisión, recall y F1 al umbral calibrado;
EMR y CER para el OCR; falsos autorizados y tiempo por decisión para el sistema.

Arquitectura completa y diagramas: [`docs/arquitectura.md`](docs/arquitectura.md).

## 4. Resultados

Preset «completo». Para el detector, el conjunto *test* (1.020 imágenes, 1.085 placas) no se usó para seleccionar hiperparámetros: los 24 ensayos se compararon en *val* y *test* se reservó para la evaluación final (`results/metrics/`).

| Componente | Métrica | Resultado | Meta |
|---|---|---|---|
| Detector YOLO11-s | mAP@0.5 | **0,972** | ≥ 0,85 ✅ |
| | mAP@0.5:0.95 | 0,693 | — |
| | Precisión / Recall / F1 (umbral 0,30) | 0,986 / 0,956 / 0,971 | — |
| | mAP@0.5:0.95 placas pequeñas / medianas / grandes | 0,481 / 0,729 / 0,744 | — |
| | Latencia (lote 1, FP16, GPU L4) | 23,3 ms (43 FPS) | — |
| Detector con hiperparámetros optimizados (Optuna, 24 *trials*) | mAP@0.5 / mAP@0.5:0.95 *test* | 0,973 / 0,704 (+0,001 / +0,011; una semilla): se mantiene el entregado | — |
| OCR (SAVH Guayaquil, 399 legibles) | EMR / CER sin filtrar por confianza | **93,7 %** / 0,010 | EMR ≥ 80 % ✅ |
| OCR (SAVH, evaluación offline al umbral anterior 0,94) | Cobertura / EMR entre aceptadas | 363/399 (91,0 %) / 349/363 (96,1 %); 14 lecturas erróneas aceptadas | — |
| OCR afinado con placas ecuatorianas (*test* separado por placa, n=86) | EMR original / afinado | 94,2 % / 94,2 % (McNemar *p* = 1,0): se mantiene el original | — |
| Regla de decisión (SAVH, lista simulada) | Falsos autorizados / rechazos indebidos | 0 de 202 / 1 de 197 | — |
| Sistema (video de la garita) | Tiempo por decisión (detección + OCR) | 99 ms | ≤ 1 s ✅ |
| Sistema | EMR punta a punta en video | pendiente: faltan etiquetas de placa para los videos de prueba | ≥ 80 % |

La aplicación usa un umbral operativo de confianza OCR de **99 %**; las lecturas por debajo pasan a verificación manual. La evaluación offline con 0,94 usa predicciones OCR guardadas y referencias SAVH: 330 lecturas confirmadas y 69 sugerencias aún no confirmadas. Es una evaluación de la configuración anterior, no una medición del rendimiento de la aplicación con el umbral actual. El 93,7 % es el EMR sin aplicar umbral; 96,1 % es el EMR solo entre lecturas aceptadas a 0,94.

**Comparación con un *baseline*.** En el mismo split de validación, YOLO11-s pasó de mAP@0.5 = 0,848 después de
la época 1 a 0,971 en la época 40 (+0,123). En el *test* separado, el modelo final obtuvo 0,972; no se compara
ese valor con la primera época porque corresponden a splits distintos. En el OCR, el *baseline* es el mismo
fast-plate-ocr sin la normalización ecuatoriana: solo con limpieza de texto logra 93,5 % de EMR en SAVH y con
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

Usuarios de demostración: `operador`, `supervisor` y `admin`; la contraseña actual para los tres perfiles es `sirap2026`. Puede cambiarse en el despliegue mediante el secreto `SIRAP_DEMO_PASSWORD`.

| Tarea | Comando |
|---|---|
| Desarrollo con recarga en caliente | `uvicorn api.main:app --reload` y, en otra terminal, `cd frontend && npm run dev` (http://localhost:5173) |
| Docker (API + interfaz) | `docker build -t sirap:1.0 . && docker run -p 7860:7860 -e SIRAP_JWT_SECRET=... sirap:1.0` → http://localhost:7860 |
| Documentación interactiva de la API | http://localhost:8000/docs (Swagger) |
| Pruebas (unitarias, integración y API) | `pip install -r requirements-dev.txt && pytest` |
| Exportar los pesos entrenados a ONNX | `python -m src.train --export-only models/best_model.pt` |
| Reentrenar (no hace falta) | `ROBOFLOW_API_KEY=... python -m src.train --roboflow --force` |
| Evaluar el detector en *test* | `python -m src.evaluate detector --data <data.yaml>` |

**Configuración:** parámetros en [`config/config.yaml`](config/config.yaml); secretos en variables de entorno
(plantillas [`.env.example`](.env.example) y [`api/.env.example`](api/.env.example)): `SIRAP_JWT_SECRET`,
`SIRAP_DEMO_PASSWORD`, `SIRAP_DATA_GITHUB_TOKEN` y, si se conecta una barrera física, `BARRERA_URL` y `BARRERA_TOKEN`.
En el Space, `SIRAP_DATA_GITHUB_TOKEN` y `SIRAP_DATA_GITHUB_REPO` respaldan las tablas CSV principales en el
repositorio privado `SIRAP_datos_privados`, restaurándolas al iniciar y sincronizando cambios. Es un proceso distinto
de la exportación enriquecida opcional, que usa `GITHUB_TOKEN` y `GITHUB_DATA_REPOSITORY` para guardar eventos en
`data/detecciones.csv`; esas variables no son intercambiables.

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
from src.storage import CsvStore
from src.access_control import decide_access
from src.data_processing import load_image

pipeline, store = ALPRPipeline.from_config(), CsvStore.from_environment()
rec = pipeline.recognize(load_image(open("data/samples/garita3_PBA-8901.jpg", "rb").read()))
print(rec.plate, f"{rec.ocr_confidence:.2%}")                       # PBA-8901 99.99%
print(decide_access(rec.plate, rec.ocr_confidence, store).titulo)   # ACCESO AUTORIZADO
```

## 6. Interfaz de usuario

**Aplicación web:** SIRAP usa una API en FastAPI y un frontend en Vue 3 (Vite, Pinia, Vue Router, Tailwind CSS y ECharts). Está desplegada en Hugging Face Spaces mediante Docker. Consulte la [aplicación en vivo](https://eduardoceballos-sirap.hf.space), la captura del [dashboard](docs/img/vue_dashboard.png) y la [guía de usuario](docs/manual_usuario.md).

| Módulo | Qué hace |
|---|---|
| **Inicio de sesión** | Usuario y contraseña; cada operación queda firmada por el usuario y su rol (operador, supervisor, administrador) |
| **Reconocimiento y Acceso** | Botones «Probar con un ejemplo», subir foto o cámara → caja de la placa sobre la imagen, placa, confianza OCR, recorte, resultado de acceso y datos del vehículo; registrar y abrir, reprocesar, apertura manual con motivo, registrar rechazo; corrección manual de la placa; **lecturas de la sesión** para comparar y exportar a CSV; ayuda «¿Cómo se usa esta pantalla?» |
| **Dashboard** | Ingresos, salidas, placas identificadas y alertas; gráficos interactivos (ECharts) por hora, resultado y garita |
| **Historial** | Filtros por fecha, placa, garita, resultado y movimiento; exportación CSV (supervisor y administrador) |

> **Exportación de resultados:** el botón **Exportar CSV** descarga las operaciones del Historial que coinciden con los filtros aplicados. Está disponible para Supervisor y Administrador.
| **Administración** | Vehículos, listas blanca/restringida con vigencia, propietarios, garitas, usuarios con contraseña; datos de demostración |
| **Acerca del modelo** | Funcionamiento, métricas, entrenamiento, optimización y **limitaciones y advertencias** |

La API consulta el servicio público del SRI para completar marca/modelo/año; también consulta EcuadorLegalOnline y
puede recibir el nombre público asociado a la placa, aunque el panel actual no lo muestra. Ninguna consulta interviene
en la decisión de acceso. La exportación enriquecida separada puede guardar ese resultado en `data/detecciones.csv`
si se configura con sus propias variables de GitHub.

**Requisitos de la interfaz cubiertos:** validación de entradas (tipo, tamaño y resolución de imagen en el servidor;
formato de placa), indicador de carga, mensajes de error comprensibles (sin trazas técnicas), confianza OCR y de
detección, visualizaciones (caja sobre la imagen, recorte, gráficos), ejemplos precargados, diseño adaptable a
celular, **tema claro/oscuro** (botón sol/luna), historial y comparación de las lecturas de la sesión y exportación CSV.

| Reconocimiento (anotado en el manual) | Dashboard | Tema oscuro | Celular |
|---|---|---|---|
| <img src="https://raw.githubusercontent.com/eduardoceballos666/SIRAP_2/396855f38f95c209d201768d6e31312dc7d41203/docs/img/vue_reconocimiento.png" width="300"> | <img src="docs/img/vue_dashboard.png" width="300"> | <img src="docs/img/vue_verificacion.png" width="300"> | <img src="docs/img/vue_movil.png" width="110"> |

### 6.1 API REST

Documentación interactiva (Swagger) en [`/docs`](https://eduardoceballos-sirap.hf.space/docs).

| Endpoint | Rol | Uso |
|---|---|---|
| `POST /api/auth/login` · `GET /api/auth/me` | — | Inicio de sesión (JWT con rol, 12 h) |
| `POST /api/recognize` | todos | Imagen → placa, confianza, caja, recorte y decisión (no registra) |
| `POST /api/plates/verify` | todos | Verificar una placa escrita o corregida a mano |
| `POST /api/plates/vehicle-data` · `GET /api/plates/vehicle-data/{request_id}` | todos | Consulta asíncrona al SRI y EcuadorLegalOnline; entrega datos complementarios de la placa, sin cambiar la decisión de acceso |
| `POST /api/operations` | todos | El operador inicia el registro y solicita la apertura; el servidor recalcula la decisión y solo permite la apertura automática si está AUTORIZADO. La apertura manual de contingencia exige motivo; SIRAP ejecuta la orden |
| `GET /api/operations` · `/api/operations/export.csv` | todos · supervisor/admin | Historial filtrado y exportación CSV |
| `GET /api/dashboard` | todos | Indicadores y datos de los gráficos |
| `GET /api/admin/{table}` | todos los usuarios autenticados | Consultar las tablas de vehículos, propietarios, autorizaciones, garitas y usuarios |
| `POST/PUT/DELETE /api/admin/...` | administrador | Crear o modificar vehículos, autorizaciones, garitas, usuarios y datos de demostración |
| `GET /api/system` · `/api/model/info` · `/api/samples` | todos | Estado, métricas del modelo e imágenes de ejemplo |

La API permite que cualquier usuario autenticado, incluido el Operador, consulte las tablas de Administración mediante `GET /api/admin/{table}`. La pantalla y la ruta de Administración en la interfaz están disponibles solo para Supervisor y Administrador. Consultar las tablas por API no concede permisos de modificación: las operaciones de escritura requieren el rol Administrador.

### 6.2 Despliegue

El workflow [`.github/workflows/deploy-hf-space.yml`](.github/workflows/deploy-hf-space.yml) publica en el Space
`eduardoceballos/sirap` cuando un push a `main` modifica alguna ruta incluida en sus filtros, o cuando se inicia
manualmente desde *Actions → Run workflow*. No cualquier cambio en `main` inicia un despliegue: cambios solo en
documentación, notebooks o pruebas no coinciden con esos filtros. Los cambios relevantes incluyen `api/**`,
`src/**`, `frontend/**`, `config/**`, `data/**`, `models/**`, `results/metrics/**`, `requirements.txt`,
`Dockerfile`, `deploy/huggingface/**` y el propio workflow. Hugging Face construye el [`Dockerfile`](Dockerfile)
(frontend compilado + API, puerto 7860). Configuración en GitHub → *Settings → Secrets and variables → Actions*:

| Nombre | Tipo | Valor |
|---|---|---|
| `HF_TOKEN` | Secret (obligatorio) | Token de Hugging Face con permiso **Write** |
| `SIRAP_JWT_SECRET` | Secret (recomendado) | Cadena larga y aleatoria para firmar las sesiones |
| `SIRAP_DEMO_PASSWORD` | Secret (opcional) | Define la contraseña común de las cuentas de demostración; el despliegue actual usa `sirap2026` |
| `SIRAP_DATA_GITHUB_TOKEN` | Secret (obligatorio para despliegues) | Token fine-grained con acceso Contents: Read and write solo a `SIRAP_datos_privados`; Actions lo valida y lo guarda automáticamente como secreto del Space para que la API respalde los CSV. |
| `HF_SPACE` | Variable (opcional) | Otro Space, p. ej. `usuario/sirap` |

**Despliegue actual:** SIRAP se aloja como una Space Docker en [Hugging Face Spaces](https://huggingface.co/spaces/eduardoceballos/SIRAP), en el puerto 7860. Hugging Face indica que ejecutar Spaces Docker requiere un plan de pago; el costo del hardware depende del recurso seleccionado ([detalle de hardware](https://huggingface.co/docs/hub/spaces-overview#hardware-resources)). La infraestructura de demostración documentada usa 2 vCPU y no tiene GPU dedicada. La API ocupa aproximadamente 410 MB de RAM con los modelos cargados. El despliegue automático requiere los secretos `HF_TOKEN` y `SIRAP_DATA_GITHUB_TOKEN`; también se recomienda configurar `SIRAP_JWT_SECRET`.

> **Estado:** prototipo funcional. La barrera es **simulada** y la base de demostración contiene **datos ficticios**.
> El Space tiene configurado el respaldo de sus tablas CSV en el repositorio privado `SIRAP_datos_privados`.
> Para operar en una garita real faltan una cámara IP integrada y el controlador físico de la barrera.

## 7. Estructura del proyecto

```
SIRAP_2/
├── .github/workflows/       # Despliegue en Hugging Face Spaces
├── api/                     # API REST con FastAPI
├── app/                     # Interfaz alternativa con Streamlit
├── config/                  # Configuración sin secretos
├── data/
│   ├── processed/           # Datos CSV de ejecución
│   ├── raw/
│   └── samples/             # Imágenes de ejemplo
├── deploy/huggingface/      # Publicación del Space
├── docs/
│   ├── img/                 # Capturas e imágenes
│   └── ...                  # Manual y documentación técnica
├── frontend/                # Interfaz Vue 3
├── models/                  # Modelos y pesos
├── notebooks/               # Análisis, entrenamiento y evaluación; incluye SIRAP_backend.ipynb
├── results/                 # Figuras, métricas e informes
├── src/                     # Modelo, OCR, decisiones y almacenamiento
├── tests/                   # Pruebas
├── Videos_Imagenes_Prueba/  # Recursos para probar el software
├── app.py                   # Lanzador compatible de app/app.py
├── Dockerfile
├── LICENSE
├── manual_usuario.pdf
├── README.md
├── requirements.txt
└── requirements-dev.txt
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
| **Eduardo Alejandro Ceballos Jijón** | Modelado y entrenamiento de YOLO11-s y OCR (fast-plate-ocr).  Desarrollo de la intefaz web Vue 3|
| **Christian Xavier Valle Maridueña** | Datos (SAVH Guayaquil e imágenes de la garita) y desarrollo de la interfaz web Vue 3 |

*Maestría en Inteligencia Artificial — Proyecto Integrador en IA (MIAR0545), 2026.*

## 10. Licencia

Código bajo licencia [MIT](LICENSE). Los pesos entrenados con Ultralytics están sujetos a su licencia AGPL-3.0;
el dataset de Roboflow es CC BY 4.0; OpenCV 4.x se distribuye bajo Apache 2.0. Consulta [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) para atribuciones y condiciones adicionales. Las atribuciones y condiciones de los demás componentes y recursos se detallan en [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## 11. Agradecimientos y referencias

### Agradecimientos

A **Gladys María Villegas Rugel**, por la dirección y asesoría académica; a la empresa que autorizó la toma de imágenes en su garita y a los docentes del programa. Los autores y sus contribuciones se presentan en la [sección 9](#9-autores-y-contribuciones).

### Componentes de software

SIRAP integra componentes de terceros para detección, OCR, procesamiento de imágenes y datos, seguimiento de video, API, interfaz web y consultas de información pública:

- **Detección y OCR:** [Ultralytics YOLO11](https://docs.ultralytics.com/models/yolo11/) y [fast-plate-ocr](https://github.com/ankandrew/fast-plate-ocr).
- **Entrenamiento e inferencia:** [PyTorch](https://pytorch.org/) se utiliza en el entorno de entrenamiento; la aplicación desplegada ejecuta el modelo exportado mediante [ONNX Runtime](https://onnxruntime.ai/).
- **Imágenes y datos:** [OpenCV](https://github.com/opencv/opencv) (`opencv-python-headless` 4.12.0.88; Apache 2.0) se usa para redimensionar imágenes y codificar JPEG; la detección la realiza YOLO11. [Pillow](https://python-pillow.org/), [NumPy](https://numpy.org/) y [Pandas](https://pandas.pydata.org/) complementan el procesamiento.
- **Seguimiento de video:** [OC-SORT](https://github.com/noahcao/OC_SORT), [Roboflow Trackers](https://github.com/roboflow/trackers) y [Roboflow Supervision](https://github.com/roboflow/supervision).
- **API y servidor:** [FastAPI](https://fastapi.tiangolo.com/) y [Uvicorn](https://www.uvicorn.org/).
- **Interfaz web:** [Vue 3](https://vuejs.org/), [Vite](https://vite.dev/), [Pinia](https://pinia.vuejs.org/), [Vue Router](https://router.vuejs.org/), [Apache ECharts](https://echarts.apache.org/), [Vue ECharts](https://github.com/ecomfe/vue-echarts) y [Tailwind CSS](https://tailwindcss.com/).
- **Consulta de información pública:** [Playwright](https://playwright.dev/) y [Chromium](https://www.chromium.org/).

Las marcas, derechos y licencias de los componentes de terceros pertenecen a sus respectivos titulares. La licencia MIT del código de SIRAP, la licencia aplicable a los pesos de Ultralytics y la licencia del dataset de Roboflow se indican en la [sección 10](#10-licencia).

### Datos y recursos del proyecto

- [Roboflow Universe — License Plate Recognition](https://universe.roboflow.com/roboflow-universe-projects/license-plate-recognition-rxg4e) (dataset utilizado para entrenar y evaluar el detector; licencia CC BY 4.0).
- [SAVH Guayaquil ANPR Plate Images Dataset — Zenodo](https://zenodo.org/records/21120307) (el registro no muestra una licencia para este archivo específico).
- **Código fuente:** [GitHub — eduardoceballos666/SIRAP_2](https://github.com/eduardoceballos666/SIRAP_2).
- **Plataforma de despliegue:** [Hugging Face Spaces — eduardoceballos/SIRAP](https://huggingface.co/spaces/eduardoceballos/SIRAP).
- **Aplicación en vivo:** [eduardoceballos-sirap.hf.space](https://eduardoceballos-sirap.hf.space).

## 12. Videos

- 🎬 **Video pitch (5 min):** _pendiente de grabación y publicación_
- 🎤 **Video de respuestas a las preguntas:** _pendiente de grabación y publicación_
