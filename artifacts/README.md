# Artefactos pesados de SIRAP

El notebook no incrusta videos ni archivos grandes. El repositorio conserva el código, las referencias necesarias, las métricas agregadas y los gráficos pequeños; los medios pesados se publican como artefactos independientes.

## Inventario

| Artefacto | Estado | Uso |
|---|---|---|
| `video_camiones.mp4` (459.3 MB) | Publicado como asset del Release [`datos-garita-v1`](https://github.com/eduardoceballos666/SIRAP_2/releases/tag/datos-garita-v1). La sección 0 lo descarga a `artifacts/video_camiones.mp4` y comprueba el tamaño y el SHA-256. | Video fuente de las secciones 6.1, 6.9 y 7.2. |
| Videos anotados que genere la sección 6.9 | Se guardan en `/content/SIRAP_workspace` durante la sesión de Colab; no se incrustan ni se publican automáticamente. | Descarga el resultado desde el panel Files de Colab. Si necesitas compartirlo, publícalo como asset de un Release aparte. |
| Imágenes y referencia de garita | Las 21 imágenes y `garita/ground_truth.csv` están versionadas en `garita/`. | Entradas de la evaluación por imagen 7.3; describen esta muestra, no la evaluación completa del video. |
| Dataset SAVH y modelo YOLO11-s | Versionados bajo `evidence/savh/` y `models/`. | Insumos del análisis y del detector. |

La sección 0 clona el repositorio y descarga el video directamente desde el Release público; no monta Google Drive. Para descargar el dataset Roboflow, configura `ROBOFLOW_API_KEY` en Secrets de Colab. Las salidas nuevas permanecen en el espacio temporal de Colab hasta que las descargues. La evaluación 7.2 continúa siendo provisional hasta completar y revisar de forma independiente la referencia de intervalos del video.
