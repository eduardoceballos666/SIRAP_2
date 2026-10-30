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

**Fuente única en producción:** el repositorio privado [SIRAP_datos_privados](https://github.com/eduardoceballos666/SIRAP_datos_privados). Los seis CSV principales que maneja `src/storage.py` y el CSV separado de detecciones enriquecidas (siete archivos en total) se guardan allí, no en el repositorio público:
- `data/processed/vehiculos.csv`, `autorizaciones.csv`, `operaciones.csv`;
- `data/processed/usuarios.csv`, `garitas.csv`, `credenciales.csv` (solo hashes de contraseñas);
- `data/processed/detecciones.csv` (exportación enriquecida; usa el mismo secreto).

`SIRAP_DATA_GITHUB_TOKEN` y `SIRAP_DATA_GITHUB_REPO` dan acceso a ese repositorio.
En Docker se exige `SIRAP_GITHUB_REQUIRED=1`: si falta GitHub, algún CSV histórico o el token,
**la aplicación no debe arrancar con datos locales desactualizados ni crear tablas vacías**.
Las lecturas se hacen contra la última versión de GitHub; las escrituras requieren el SHA de la
versión previamente leída, rechazando cambios concurrentes en vez de sobrescribir registros ajenos.
La carpeta local del hosting es una copia efímera de trabajo, nunca la fuente de verdad.

**Protección previa a la migración:** rama privada
`respaldo-pre-migracion-2026-10-30` con los seis CSV originales.
La rama `main` privada conserva las filas históricas; solo se ha agregado el CSV de detecciones,
que no existía allí. No borrar el respaldo. La exportación pública antigua
`data/detecciones.csv` (solo encabezados cuando se inspeccionó) no se usa para nuevos eventos;
cualquier histórico de instalaciones anteriores que usara otro repositorio sigue sin modificarse.

**Al cambiar de hosting:** configurar el mismo secreto, repo y `SIRAP_GITHUB_REQUIRED=1`
en el nuevo servidor, mantener `data/processed/` como caché escribible y arrancar.
La configuración de GitHub sigue siendo la fuente persistente. La demo usa datos ficticios;
no copie datos reales al repositorio público.

**Limitaciones:** GitHub Contents API tiene latencia y conflictos de versión; si falla,
SIRAP debe rechazar escrituras y aperturas en vez de guardar solo localmente. Para mucho tráfico
concurrente es recomendable migrar a una base de datos transaccional privada. El notebook
de entrenamiento guarda artefactos y CSV de experimentos en Google Drive; no forman parte
del almacenamiento operativo de la aplicación web.

## 5. Imágenes de ejemplo (`samples/`)

| Archivo | Origen | Resultado esperado |
|---|---|---|
| `garita3_PBA-8901.jpg` | Recorte de la guía de diseño `docs/img/vue_dashboard.png` (se quitó el recuadro verde) | Autorizado – lista blanca |
| `garita2_GBO-0429.jpg` | La misma imagen con la placa reemplazada (sintética) | Denegado – lista restringida |
| `garita1_GSA-1234.jpg` | La misma imagen con la placa reemplazada (sintética) | No registrado |
| `garita3_PCD-5678_desenfocada.jpg` | Placa reemplazada y desenfoque gaussiano (sintética) | Verificación manual (confianza baja) |

> Estas imágenes **no** son capturas reales ni forman parte de la evaluación: existen para probar la interfaz. Las
> métricas del modelo se calculan con los splits de *test* y con SAVH Guayaquil.

## Umbral operativo OCR

La aplicación usa **94 %** como umbral operativo. Se eligió considerando la capacidad de procesamiento limitada del hosting documentado de Hugging Face (2 vCPU y sin GPU dedicada): al aceptar antes una lectura estable, la interfaz puede terminar el análisis de video sin procesar cuadros adicionales. El umbral no acelera cada inferencia; el ahorro potencial proviene de analizar menos cuadros. También busca reducir verificaciones manuales. En videos y cámaras, la misma placa debe alcanzar al menos 94 % en dos cuadros muestreados, separados por 1 segundo; si la lectura queda por debajo del umbral o los cuadros no coinciden, se solicita validación manual al terminar el análisis. En una imagen estática se evalúa el cuadro disponible.

Al alcanzar el 94 %, el servidor declara la placa autorizada solo si tiene una autorización vigente en la lista blanca y no está restringida. La barrera no se acciona solo por reconocer la placa: el operador debe solicitar la apertura.
