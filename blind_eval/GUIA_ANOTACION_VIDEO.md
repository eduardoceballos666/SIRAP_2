# Guía humana de anotación y revisión del video SIRAP

> **Referencia final:** [`video_ground_truth.csv`](video_ground_truth.csv) es el archivo usado por la sección 7.2. Su procedencia y sus límites están descritos en [`video_ground_truth_review.md`](video_ground_truth_review.md). Esta guía está dirigida a una persona que anote o revise el video; no modifica ni oculta cómo se produjo la referencia actualmente publicada.

## Propósito

Esta guía permite que una persona transcriba placas visibles y marque sus intervalos de legibilidad de forma reproducible e independiente de las predicciones del sistema. La anotación humana debe basarse en el video, no en el OCR.

## Acceso y preparación

1. Abre el notebook en Colab y conecta un runtime GPU disponible.
2. Ejecuta la sección 0: clona el repositorio, descarga `video_camiones.mp4` del Release `datos-garita-v1` y prepara las rutas.
3. Ejecuta las celdas previas requeridas por el notebook y, para inspeccionar el video, corre la sección 6 en orden.
4. Si la evaluación es solo de reconocimiento, desactiva en la configuración del pipeline las consultas externas al SRI y al sitio de propietarios antes de ejecutar la sección 6.

## Procedimiento de anotación humana

1. Recorre el video completo y localiza todos los vehículos, incluidos los que el detector no encontró. La hoja de contactos y la guía por evento pueden ayudar a navegar, pero no deben usarse como etiquetas.
2. Para cada placa que puedas leer directamente, transcribe los caracteres y marca el primer y el último cuadro en que se leen con seguridad. La numeración empieza en cero y debe corresponder al mismo `video_camiones.mp4`.
3. Crea una fila por placa y por pasada. Si dos vehículos aparecen a la vez, registra cada placa por separado.
4. Si un carácter o una placa no se distinguen con seguridad, no adivines ni copies el OCR. Anota el caso aparte para su revisión.
5. Revisa cada límite con `ver_cuadros(desde, hasta)` en Colab. Para una anotación nueva, empieza desde `video_ground_truth_template.csv`; no sobrescribas la referencia publicada sin revisión y documentación del cambio.
6. Para una revisión independiente, la persona revisora debe ver el video sin consultar las predicciones, el OCR ni las lecturas de la anotación anterior. Registra desacuerdos y su resolución aparte.

## Columnas del CSV

| Columna | Contenido |
|---|---|
| `plate_gt` | Placa transcrita desde el video, con o sin guion; el notebook la normaliza. |
| `frame_start` | Primer cuadro en que la placa resulta legible. Entero, desde 0. |
| `frame_end` | Último cuadro en que la placa resulta legible. Entero, inclusivo. |

Plantilla:

```csv
plate_gt,frame_start,frame_end
```

## Evaluación y resultados

1. Ejecuta la sección 7.2 después de preparar la referencia. El notebook valida el formato, los límites y los solapamientos antes de asociar cada lectura con la placa visible en su cuadro.
2. Conserva la referencia, el registro de decisiones de la sección 6.9, el JSON de métricas y el video anotado como artefactos de una misma corrida.
3. Reporta por separado EMR por lectura, recall de placas reales, falsos autorizados, latencia y lecturas por placa. Las métricas de clips cortos a 1 fps no sustituyen la evaluación del video completo ni la evaluación del pipeline con OC-SORT.

## Estado y procedencia de la referencia publicada

El archivo [`video_ground_truth.csv`](video_ground_truth.csv) contiene 20 pasadas legibles con intervalos inclusivos en el video completo (cuadros 0 a 18.114). Su procedencia, las decisiones de cotejo, las limitaciones y la falta de una revisión humana independiente están documentadas en [`video_ground_truth_review.md`](video_ground_truth_review.md). Esta guía está escrita para orientar anotaciones y revisiones humanas; esa descripción no debe confundirse con la procedencia del archivo publicado.

Los archivos `video_ground_truth_points_provisional.csv` (18 cuadros puntuales) y `video_ground_truth_intervals_provisional.csv` (borrador de intervalos) son históricos y no deben usarse en 7.2.