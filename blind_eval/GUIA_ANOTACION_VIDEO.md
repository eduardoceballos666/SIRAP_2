# Guía de anotación independiente del video SIRAP

## Objetivo

Crear la referencia humana que necesita la sección 7 del notebook para evaluar el pipeline completo de YOLO11 → OC-SORT → OCR. La anotación debe reflejar lo que una persona puede leer en el video, no lo que predijo el sistema.

## Acceso y preparación

1. Inicia sesión en Colab desde la pestaña compartida y conecta un runtime GPU disponible.
2. Ejecuta la sección 0 para montar `MyDrive/proyecto_integrador_placas` y comprobar que `video_camiones.mp4` está presente.
3. Ejecuta las celdas previas que exige la portada del notebook y luego la sección 6 en orden hasta generar el registro de decisiones y el video anotado.
4. Si la evaluación es solo de reconocimiento, desactiva en la configuración del pipeline las consultas externas al SRI y al sitio de propietarios antes de ejecutar la sección 6. El análisis de placas no requiere esas consultas.

## Anotación de verdad de referencia

1. Abre la sección 7.1. Usa la hoja de contactos del video para encontrar todos los vehículos, incluidos los que el detector no registró. La guía por evento ayuda a revisar el intervalo; no uses la lectura OCR como etiqueta.
2. Para cada placa legible, transcribe manualmente los caracteres y marca el primer y último número de cuadro en que la placa se puede leer. La numeración empieza en cero y debe corresponder al mismo `video_camiones.mp4` procesado en la sección 6.
3. Escribe una fila por placa y por pasada del vehículo. Si coinciden dos vehículos, anota cada placa en su propia fila. Usa la plantilla `video_ground_truth_template.csv`.
4. Si una placa no se puede leer con seguridad, no inventes la etiqueta ni la copies del OCR; deja constancia en las notas de revisión fuera del CSV evaluable y solicita una segunda revisión humana.
5. Revisa los límites de cada intervalo con `ver_cuadros(desde, hasta)` en Colab. Guarda la referencia como `MyDrive/proyecto_integrador_placas/video_ground_truth.csv` y conserva una copia versionada antes de reemplazar una referencia existente.

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

Se revisaron visualmente 44 cuadros guía y se guardó una anotación provisional de 18 placas legibles en `video_ground_truth.csv`. Cada fila es un cuadro puntual, no el intervalo completo de legibilidad ni un inventario exhaustivo de vehículos. La evaluación completa de 7.2 sigue pendiente de delimitar esos intervalos, buscar vehículos omitidos y obtener una segunda revisión humana. El detalle está en `video_ground_truth_review.md`.
