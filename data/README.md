# Datos de SIRAP

| Carpeta | Contenido | ¿En el repositorio? |
|---|---|---|
| `raw/` | Datasets originales descargados (Roboflow, SAVH) | No (pesados; se descargan con el notebook o `src/train.py --roboflow`) |
| `processed/` | Base SQLite de demostración (`sirap_demo.db`, se crea sola) y CSV procesados | Solo CSV livianos |
| `samples/` | Imágenes de ejemplo que usa la app («Prueba con un ejemplo») | Sí |

## 1. Detección de placas – *License Plate Recognition* (Roboflow Universe)

- **Fuente:** `roboflow-universe-projects/license-plate-recognition-rxg4e`, versión 11.
- **Licencia:** CC BY 4.0.
- **Tamaño:** 10 125 imágenes — 7 057 *train*, 2 048 *val*, 1 020 *test* — con una sola clase (`License_Plate`).
- **Formato:** YOLO (una caja normalizada por placa en `labels/*.txt`).
- **Uso:** entrenar y evaluar el detector YOLO11-s. No es específico de Ecuador: enseña a detectar placas en general.
- **Placas de *test* por tamaño (criterio COCO):** 191 pequeñas (< 32² px), 756 medianas, 138 grandes (≥ 96² px).

## 2. OCR y validación local – SAVH Guayaquil (Zenodo)

- **Fuente:** *SAVH Guayaquil ANPR Plate Images Dataset* (público en Zenodo): 2 000 imágenes de placas
  ecuatorianas capturadas en Guayaquil.
- **Subconjunto usado:** `savh_ground_truth_subset.zip`, 739 recortes con la lectura de la cámara en
  `ground_truth.csv`. Esa lectura se revisó a mano (hoja «Revisión placas SAVH (142 legibles)») porque la cámara
  confunde caracteres (ej. `GB01825` es `GBO-1825`).
- **Uso:** medir el OCR (EMR y CER) con placas reales del país y estudiar su confianza.

## 3. Imágenes de la garita (propias)

Imágenes y video del punto de control tomados en una planta **con autorización escrita** de la empresa. Contienen
placas reales, por eso **no se publican**: se guardan en el Drive del proyecto y se usan solo para la evaluación
punta a punta (sección 7 del notebook).

## 4. Autorizaciones y registros del pipeline

El notebook usa `authorized_plates.csv` en la carpeta de Drive como lista de placas autorizadas. Guarda lecturas,
consultas SRI y resultados del propietario en archivos CSV bajo `registros_csv/`. Si se configura un repositorio
privado de GitHub en los Secrets de Colab, las detecciones enriquecidas se sincronizan en `data/detecciones.csv`.
El notebook no necesita un servicio PostgreSQL para este flujo.

La aplicación mantiene su almacenamiento de demostración separado en SQLite y usa `sql/seed_demo.sql` con datos
ficticios; ese esquema no contiene la lista de vehículos de la planta.

## 5. Imágenes de ejemplo (`samples/`)

| Archivo | Origen | Resultado esperado |
|---|---|---|
| `garita3_PBA-8901.jpg` | Recorte de la guía de diseño `docs/img/SIRAP_Dashboard.png` (se quitó el recuadro verde) | Autorizado – lista blanca |
| `garita2_GBO-0429.jpg` | La misma imagen con la placa reemplazada (sintética) | Denegado – lista restringida |
| `garita1_GSA-1234.jpg` | La misma imagen con la placa reemplazada (sintética) | No registrado |
| `garita3_PCD-5678_desenfocada.jpg` | Placa reemplazada y desenfoque gaussiano (sintética) | Verificación manual (confianza baja) |

> Estas imágenes **no** son capturas reales ni forman parte de la evaluación: existen para probar la interfaz. Las
> métricas del modelo se calculan con los splits de *test* y con SAVH Guayaquil.
