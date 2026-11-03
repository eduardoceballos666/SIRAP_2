# Evaluación punta a punta con las imágenes de la garita

Fecha de ejecución: 2026-11-01. Notebook SIRAP_backend.ipynb, sección 7.3, detector YOLO11-s y OCR fast-plate-ocr.

| Métrica | Resultado |
|---|---:|
| Imágenes evaluadas | 21 |
| Detección de placa | 19/21 (90.5%) |
| Coincidencia exacta de placa (EMR) | 8/21 (38.1%) |
| Salidas con formato ecuatoriano válido | 16/21 (76.2%) |
| Latencia media por imagen | 37.69 ms |
| Latencia p95 por imagen | 37.78 ms |
| Detección media | 20.18 ms |
| Falsos autorizados reportados | 0 |

El EMR usa las 21 imágenes como denominador; una imagen sin detección o con texto distinto cuenta como error. La corrida cubre detección → OCR → normalización → decisión por imagen. Las imágenes no tienen dimensión temporal, por lo que esta prueba no evalúa OC-SORT ni el seguimiento de vehículos.

Alcance y publicación: las 21 imágenes y la referencia fila por fila están publicadas en `garita/imagenes/` y `garita/ground_truth.csv`. El registro detallado de predicciones no aparece entre los archivos versionados. El informe registra que la lista de autorizaciones estaba vacía en esta corrida. El archivo `data/authorized_plates.csv` está poblado en el repositorio actual; por eso, el cero reportado no prueba el comportamiento con la lista actualmente publicada. Esta muestra no es una evaluación ciega independiente ni del video completo.

El EMR de esta corrida queda por debajo de la meta del proyecto de 80%. Debe analizarse solo como desempeño de esta muestra; no se deben inferir métricas de intervalos, pasadas o vehículos omitidos en el video.

## Registro distinto en la salida guardada del notebook

La salida guardada de la celda 7.3 de `notebooks/SIRAP_backend.ipynb` corresponde a otra ejecución: 21 imágenes, detección 19/21, EMR 9/21 (42,9 %), formato válido 16/21, latencia media 1,400674 s por imagen, p95 1,905149 s y detección media 1,33666 s. El notebook no conserva una fecha ni un identificador que permita ordenarla con certeza respecto de la corrida de este informe. Se mantienen como mediciones distintas y no se combinan.

La reejecución más reciente de video 6.9/7.2 obtuvo EMR 18/30 (60 %), recall de placas únicas 16/17 (94,12 %) y 2/30 falsas autorizaciones observadas entre lecturas clasificables. Veintiuna lecturas no tienen referencia y dos pasadas dudosas siguen excluidas; la tasa integral no es estimable. La corrida guardada anterior (17/24; 0/24) está descrita por separado en el [informe de video](video_e2e_intervalos_final.md).

