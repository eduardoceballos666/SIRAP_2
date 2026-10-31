# Validación ciega SAVH y evaluación de video

Fecha: 2026-10-30. Inferencia local con el detector ONNX de SIRAP y ONNX Runtime CPU. Los videos e imágenes se procesaron localmente.

Actualización: 2026-10-30, ejecución del video completo en Colab con GPU L4.

## Validación ciega independiente de imágenes SAVH

Se seleccionaron aleatoriamente 58 imágenes fuera de las 330 registradas en `particion.csv` (semilla 20261030), con cero solapamiento. Las predicciones se generaron antes de abrir la referencia SAVH cerrada y aprobada por humanos: solo se incluyeron filas con `aplicable_evaluacion=SI` y `aprobacion_humana=ok`. Se puntuaron 57 imágenes. Se excluyó C015 porque no aparece en esa referencia aprobada; no se usó el nombre del archivo como etiqueta.

| OCR | Exactas | Cobertura | CER agregado | Latencia media/imagen |
|---|---:|---:|---:|---:|
| Base `cct-s-v2-global-model` | 42/57 (73.7%) | 56/57 (98.2%) | 5.4% | 170 ms |
| Afinado SAVH | 35/57 (61.4%) | 56/57 (98.2%) | 7.1% | 172 ms |

La métrica primaria es coincidencia exacta tras normalizar a letras y números. CER es la suma de distancias de edición dividida por el número de caracteres de referencia. En esta muestra, el OCR base superó al afinado. Esta constituye una evaluación ciega de holdout frente a referencias aprobadas por humanos; no se usaron para entrenar el detector ni el OCR. La muestra mide generalización sobre 57 imágenes independientes del split de afinamiento; C015 se dejó fuera por no tener fila en la referencia cerrada.

## Video, extremo a extremo

Se procesaron cuatro clips a 1 fotograma por segundo con el detector y el OCR base. El pipeline Python por fotograma no incluyó OC-SORT. Las etiquetas visuales de dos clips fueron transcritas por un único evaluador de IA; por tanto, los números siguientes son exploratorios y necesitan confirmación humana.

| Video | Duración | Frames | Lecturas válidas | Referencia visual | Coincidencia exacta |
|---|---:|---:|---:|---|---:|
| IMG_2606.mp4 | 51.0 s | 51 | 46 | No legible | No evaluable |
| IMG_2609.mp4 | 21.3 s | 22 | 10 | No legible | No evaluable |
| IMG_2626.mp4 | 19.4 s | 20 | 12 | Legible; placa omitida | 10/20 |
| IMG_2632.mp4 | 15.7 s | 16 | 14 | Legible; placa omitida | 12/16 |

### Video completo con YOLO11 y OC-SORT (31-10-2026)

Se ejecutó en Colab el pipeline completo sobre `video_camiones.mp4`, a resolución 1280×720 y 30 fps, procesando los 18.115 cuadros. La celda terminó en 409,6 s, incluidos el cierre y la escritura de salidas; la tasa medida del pipeline fue 61,77 cuadros/s.

| Métrica operativa | Resultado |
|---|---:|
| Tracks confirmados | 52 |
| Lecturas OCR emitidas | 52 |
| Tracks sin lectura | 0 |
| Lecturas con formato ecuatoriano válido | 25 |
| Llamadas a OCR | 225 |
| Detección media por cuadro | 14,51 ms |
| Seguimiento medio por cuadro | 0,45 ms |
| Detección + OCR por decisión | 91,99 ms |
| Throughput del pipeline | 61,77 cuadros/s |

Las consultas al SRI y al sitio de propietarios estuvieron desactivadas. `authorized_plates.csv` estaba vacío, así que ninguna lectura pudo autorizarse desde esa lista. Se verificaron los artefactos en `MyDrive/proyecto_integrador_placas/experimentos/license-plate-recognition-rxg4e-v11`: `videos/YOLO11_yolo11s_completo.mp4` (65.182.798 bytes), `videos/YOLO11_yolo11s_completo_vista.mp4` (1.985.537 bytes), `resultados/YOLO11_yolo11s_completo_decisions_log.csv` y `resultados/YOLO11_yolo11s_completo_video.json`.

Después se ejecutó la celda 7.2; en esa corrida confirmó que no existía `MyDrive/proyecto_integrador_placas/video_ground_truth.csv` y omitió la medición de coincidencia exacta y recall de placas. Los conteos y tiempos anteriores son métricas operativas, no precisión punta a punta.

Para facilitar la revisión sin usar las salidas OCR como etiquetas, la celda 7.1 generó una hoja visual y 44 eventos candidatos. Después se inspeccionaron visualmente los cuadros guía y se creó una referencia privada con 18 transcripciones legibles de las placas físicas. Cada fila es un cuadro puntual (`frame_start == frame_end`); no es una anotación completa de intervalos ni de todos los vehículos. El CSV y las etiquetas por fila se conservan en Drive privado; no se publican en GitHub. Se añadió `video_ground_truth_review.md` con el alcance y las tareas pendientes.

No se calculó EMR ni recall completo usando esta referencia puntual, porque esos resultados serían engañosos para el video entero. Para completar 7.2 aún hay que revisar el video original cuadro a cuadro, delimitar primer/último cuadro legible de cada pasada, añadir vehículos omitidos por los eventos detectados y solicitar una segunda revisión humana independiente. La guía operativa y la plantilla están en `blind_eval/GUIA_ANOTACION_VIDEO.md` y `blind_eval/video_ground_truth_template.csv`.

Artefactos publicados: este informe y `results/metrics/blind_independent_video_eval_20261030.json` con métricas agregadas. No se publican las matrículas de la referencia de video, predicciones por fila ni claves del holdout ciego; los materiales detallados permanecen en Drive privado para preservar la privacidad y la independencia de las evaluaciones.
