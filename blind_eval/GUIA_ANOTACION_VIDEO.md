# Guía de anotación independiente del video SIRAP

> **Referencia final:** [`video_ground_truth.csv`](video_ground_truth.csv) es el archivo final que usa la sección 7.2. Su procedencia y sus límites están en [`video_ground_truth_review.md`](video_ground_truth_review.md). Esta guía describe cómo se anota el video y sirve para revisar o rehacer esa referencia; los CSV provisionales de esta carpeta son históricos.

## Objetivo

Crear la referencia humana que necesita la sección 7 del notebook para evaluar el pipeline completo de YOLO11 → OC-SORT → OCR. La anotación debe reflejar lo que una persona puede leer en el video, no lo que predijo el sistema.

## Acceso y preparación

1. Inicia sesión en Colab desde la pestaña compartida y conecta un runtime GPU disponible.
2. Ejecuta la sección 0: clona el repositorio, descarga `video_camiones.mp4` del Release `datos-garita-v1` y copia la referencia final `blind_eval/video_ground_truth.csv` a `/content/SIRAP_workspace/video_ground_truth.csv`.
3. Ejecuta las celdas previas que exige la portada del notebook y luego la sección 6 en orden hasta generar el registro de decisiones y el video anotado.
4. Si la evaluación es solo de reconocimiento, desactiva en la configuración del pipeline las consultas externas al SRI y al sitio de propietarios antes de ejecutar la sección 6. El análisis de placas no requiere esas consultas.

## Anotación de verdad de referencia

1. Abre la sección 7.1. Usa la hoja de contactos del video para encontrar todos los vehículos, incluidos los que el detector no registró. La guía por evento ayuda a revisar el intervalo; no uses la lectura OCR como etiqueta.
2. Para cada placa legible, transcribe manualmente los caracteres y marca el primer y último número de cuadro en que la placa se puede leer. La numeración empieza en cero y debe corresponder al mismo `video_camiones.mp4` procesado en la sección 6.
3. Escribe una fila por placa y por pasada del vehículo. Si coinciden dos vehículos, anota cada placa en su propia fila. Para una anotación nueva usa la plantilla `video_ground_truth_template.csv`.
4. Si una placa no se puede leer con seguridad, no inventes la etiqueta ni la copies del OCR; deja constancia en las notas de revisión fuera del CSV evaluable y solicita una segunda revisión humana.
5. Revisa los límites de cada intervalo con `ver_cuadros(desde, hasta)` en Colab. La referencia final versionada es `blind_eval/video_ground_truth.csv`. Si una revisión posterior la cambia, reemplaza ese archivo mediante un cambio revisado y documenta el motivo en `video_ground_truth_review.md`; no la sustituyas por un borrador.

## Columnas del CSV

| Columna | Contenido |
|---|---|
| `plate_gt` | Placa transcrita desde el video, con o sin guion; el notebook la normaliza. |
| `frame_start` | Primer cuadro en que la placa resulta legible. Entero, desde 0. |
| `frame_end` | Último cuadro en que la placa resulta legible. Entero, inclusivo. |

La plantilla inicial es:

```csv
plate_gt,frame_start,frame_end
```

## Evaluación y cierre

1. Ejecuta la sección 7.2 después de guardar la referencia. El notebook valida formato, límites y solapamientos antes de asociar cada lectura del registro con la placa visible en su cuadro.
2. Conserva el CSV de referencia, el registro de decisiones de la sección 6.9, el JSON de métricas y el video anotado como artefactos de la misma corrida.
3. Reporta por separado EMR por lectura, recall de placas reales, falsos autorizados, latencia y lecturas por placa. No presentes las métricas de los cuatro clips cortos a 1 fps como sustituto del video completo ni como resultado del pipeline con OC-SORT.
4. Para que la etiqueta sea independiente, un segundo revisor debe comprobar las transcripciones y los intervalos viendo el video, sin tomar el OCR como verdad. Documenta cualquier desacuerdo y su resolución.

## Estado actual

**La referencia final está publicada en [`video_ground_truth.csv`](video_ground_truth.csv)**, con columnas `plate_gt,frame_start,frame_end`. Tiene 20 pasadas legibles, con intervalos inclusivos sobre el video completo (cuadros 0 a 18.114). Se armó con dos anotaciones ciegas del video completo, hechas con Claude (asistente de IA) en sesiones separadas. Después se cotejaron y cada discrepancia se adjudicó en el video original. Dos placas que siguieron dudosas y un fragmento sin placa visible quedaron fuera.

No hubo revisión humana independiente. Al informar las métricas de 7.2, indica esa procedencia (ver la sección de limitaciones de `video_ground_truth_review.md`). El CSV contiene placas reales y se publica intencionalmente como artefacto del proyecto.

Los archivos `video_ground_truth_points_provisional.csv` (18 cuadros puntuales) y `video_ground_truth_intervals_provisional.csv` (borrador de intervalos) son históricos y no deben usarse en 7.2. Las métricas con la referencia final quedan pendientes de ejecutar 6.9 y 7.2.
