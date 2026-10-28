# Datos de SIRAP

| Carpeta | Contenido | ¿En el repositorio? |
|---|---|---|
| `raw/` | Datasets originales descargados (Roboflow, SAVH) | No (pesados; se descargan con el notebook o `src/train.py --roboflow`) |
| `processed/` | Archivos CSV locales y CSV procesados | Solo CSV livianos |
| `samples/` | Imágenes de ejemplo que usa la app («Prueba con un ejemplo») | Sí |

## 1. Detección de placas – *License Plate Recognition* (Roboflow Universe)

- **Fuente:** `roboflow-universe-projects/license-plate-recognition-rxg4e`, versión 11.
- **Licencia:** CC BY 4.0.
- **Tamaño:** 10 125 imágenes — 7 057 *train*, 2 048 *val*, 1 020 *test* — con una sola clase (`License_Plate`).
- **Formato:** YOLO (una caja normalizada por placa en `labels/*.txt`).
- **Uso:** entrenar y evaluar el detector YOLO11-s. No es específico de Ecuador: enseña a detectar placas en general.
- **Placas de *test* por tamaño (criterio COCO):** 191 pequeñas (< 32² px), 756 medianas, 138 grandes (≥ 96² px).

## 2. OCR y validación local – SAVH Guayaquil (Zenodo)

- **Fuente:** [*SAVH Guayaquil ANPR Plate Images Dataset* (Zenodo)](https://zenodo.org/records/21120307): 2 000 imágenes de placas ecuatorianas capturadas en Guayaquil. El registro consultado no muestra licencia para este archivo específico; revise sus condiciones antes de redistribuirlo.
- **Subconjunto usado:** `savh_ground_truth_subset.zip`, 739 recortes con la lectura de la cámara en
  `ground_truth.csv`. Esa lectura se revisó a mano (hoja «Revisión placas SAVH (142 legibles)») porque la cámara
  confunde caracteres (ej. `GB01825` es `GBO-1825`).
- **Uso:** medir el OCR (EMR y CER) con placas reales del país y estudiar su confianza.

## 3. Imágenes de la garita (propias)

Imágenes y video del punto de control tomados en una planta **con autorización escrita** de la empresa. Contienen
placas reales, por eso **no se publican**: se guardan en el Drive del proyecto y se usan solo para la evaluación
punta a punta (sección 7 del notebook).

## 4. Autorizaciones y registros del pipeline

El notebook mantiene sus archivos de trabajo en `registros_csv/`; ese flujo es independiente de la aplicación web.

La aplicación web mantiene sus tablas operativas en `data/processed/*.csv` y, en el Space, las restaura y sincroniza
con el repositorio privado `SIRAP_datos_privados` mediante `SIRAP_DATA_GITHUB_TOKEN` y
`SIRAP_DATA_GITHUB_REPO`. La exportación enriquecida opcional usa `GITHUB_TOKEN` y
`GITHUB_DATA_REPOSITORY` para escribir eventos en `data/detecciones.csv`; no sustituye el respaldo de las tablas
operativas. La demo usa datos ficticios y no contiene la lista de vehículos de la planta.

## 5. Imágenes de ejemplo (`samples/`)

| Archivo | Origen | Resultado esperado |
|---|---|---|
| `garita3_PBA-8901.jpg` | Recorte de la guía de diseño `docs/img/SIRAP_Dashboard.png` (se quitó el recuadro verde) | Autorizado – lista blanca |
| `garita2_GBO-0429.jpg` | La misma imagen con la placa reemplazada (sintética) | Denegado – lista restringida |
| `garita1_GSA-1234.jpg` | La misma imagen con la placa reemplazada (sintética) | No registrado |
| `garita3_PCD-5678_desenfocada.jpg` | Placa reemplazada y desenfoque gaussiano (sintética) | Verificación manual (confianza baja) |

> Estas imágenes **no** son capturas reales ni forman parte de la evaluación: existen para probar la interfaz. Las
> métricas del modelo se calculan con los splits de *test* y con SAVH Guayaquil.

## Umbral operativo OCR

La aplicación usa un umbral de confianza OCR de **99 %**. Las lecturas por debajo pasan a verificación manual.
