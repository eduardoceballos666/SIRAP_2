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

Limitaciones: la referencia fila por fila y el registro con predicciones permanecen privados. La lista authorized_plates.csv estaba vacía, por lo que cero falsos autorizados no demuestra el comportamiento de autorización frente a una lista poblada. No se presenta esta muestra como evaluación ciega independiente ni como evaluación del video completo.

El resultado queda por debajo de la meta del proyecto de EMR ≥ 80%. Debe analizarse como desempeño de esta muestra de 21 imágenes; no se deben inferir métricas de intervalos, pasadas o vehículos omitidos en el video.

La evaluación por video de 6.9/7.2 ya se ejecutó con la referencia final `blind_eval/video_ground_truth.csv`: EMR 17/24 (70,83 %), recall de placas únicas 15/17 (88,24 %) y 0 falsas autorizaciones entre 24 lecturas clasificables. Diez lecturas no tienen referencia, así que la tasa integral no es estimable; dos pasadas dudosas quedaron excluidas. Consulta el [informe final](video_e2e_intervalos_final.md).

