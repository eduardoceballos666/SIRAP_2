# Resultados de SIRAP

Esta carpeta reúne métricas agregadas, tablas, gráficos compactos y reportes. Cada artefacto debe leerse con el protocolo y las limitaciones indicadas; una métrica de detector, OCR, imagen o video no representa por sí sola el rendimiento total de la aplicación.

| Carpeta | Contenido |
|---|---|
| [`figures/`](figures/) | Gráficos pequeños para documentación e informes. |
| [`metrics/`](metrics/) | Métricas y resultados agregados en JSON, CSV y Markdown. |
| [`reports/`](reports/) | Reportes generados. Los logs de ejecución locales se excluyen de Git. |

## Detector, entrenamiento y velocidad

| Artefacto | Contenido y alcance |
|---|---|
| [`metrics/dataset_resumen.json`](metrics/dataset_resumen.json) | Cantidad de imágenes e instancias por partición y distribución de tamaños del test. |
| [`metrics/entrenamiento.json`](metrics/entrenamiento.json) y [`metrics/entrenamiento_yolo11_results.csv`](metrics/entrenamiento_yolo11_results.csv) | Configuración, duración y resultados por época del entrenamiento YOLO11-s. |
| [`metrics/entrenamiento_yolo11_rapido.json`](metrics/entrenamiento_yolo11_rapido.json) y [`metrics/entrenamiento_yolo11_rapido_results.csv`](metrics/entrenamiento_yolo11_rapido_results.csv) | Corrida exploratoria de 15 épocas: 30 % de entrenamiento y 25 % de validación; mAP@0.5:0.95 de 0,66085. No reemplaza ni se compara como equivalente al entrenamiento completo de 40 épocas. |
| [`figures/entrenamiento_yolo11_rapido.png`](figures/entrenamiento_yolo11_rapido.png) y [`figures/yolo11_*_test_*.png`](figures/) | Curvas de la corrida rápida y gráficos de evaluación de las corridas YOLO11 completa y rápida. Las imágenes de lotes de entrenamiento/validación no se publican aquí. |
| [`metrics/detector_test.json`](metrics/detector_test.json) | mAP, precisión, recall y F1 del detector en test; P, recall y F1 usan el umbral de decisión calibrado en validación. |
| [`metrics/umbrales.json`](metrics/umbrales.json) | Umbral de confianza de detección YOLO11 calibrado con validación. No contiene el umbral OCR. |
| [`metrics/velocidad.json`](metrics/velocidad.json) | Latencias, FPS, parámetros y GFLOPs medidos para inferencia del detector en GPU. |
| [`metrics/video_garita.json`](metrics/video_garita.json) | Conteos y rendimiento operativo de la corrida del video completo. No contiene métricas de exactitud: esas se calculan en 7.2 con la referencia final [`blind_eval/video_ground_truth.csv`](../blind_eval/video_ground_truth.csv). |

### Umbrales que no deben confundirse

- El umbral de decisión del detector YOLO se calibra en validación y se publica en [`metrics/umbrales.json`](metrics/umbrales.json), alrededor de 0,30.
- La configuración actual del OCR de la aplicación define 0,94 en [`config/config.yaml`](../config/config.yaml). Las lecturas por debajo del umbral requieren verificación manual.
- El valor 0,99 mencionado en algunos análisis OCR es un umbral comparado offline; no es el valor de `umbrales.json` ni el umbral OCR configurado actualmente en la aplicación.
- [`metrics/regla_decision_savh.json`](metrics/regla_decision_savh.json) compara decisiones offline con una lista simulada. No constituye una prueba integral de acceso ni una medición con la lista real de autorizaciones.

## OCR y evaluación de referencias SAVH

Estos archivos usan subconjuntos, referencias y protocolos distintos. Sus porcentajes no se deben combinar como si fueran una sola corrida.

| Artefacto | Resultado o propósito | Alcance y limitación |
|---|---|---|
| [`metrics/ocr_savh.json`](metrics/ocr_savh.json) | Resultado histórico: 374/399 exactas (93,7 %), CER 0,010. | Incluye 69 sugerencias de etiqueta que en esa versión estaban sin confirmar. Es una métrica offline, no una validación independiente. |
| [`metrics/ocr_savh_aprobaciones_398.json`](metrics/ocr_savh_aprobaciones_398.json) | Recálculo: 388/398 exactas (97,49 %), CER 0,003649. | Condicionado a respuestas de revisión no ciegas; en algunos desacuerdos se pudieron ver sugerencias OCR. No demuestra mejora del modelo. |
| [`metrics/ocr_savh_revision_asistida_397.json`](metrics/ocr_savh_revision_asistida_397.json) | Revisión asistida de etiquetas y recálculo sobre un subconjunto de 397. | Resultado provisional de una revisión anterior; no sustituye las referencias ni la evaluación ciega. |
| [`metrics/ocr_savh_validacion_ciega_piloto.json`](metrics/ocr_savh_validacion_ciega_piloto.json) | Piloto visual de 84 imágenes del split de prueba. | No es cierre independiente: 13 discrepancias con referencias archivadas requieren adjudicación. |
| [`metrics/blind_independent_video_eval_20261030.json`](metrics/blind_independent_video_eval_20261030.json) y [reporte detallado](metrics/validacion_ciega_video_20261030.md) | Holdout ciego de OCR: 57 imágenes puntuadas; OCR base 42/57 (73,7 %) y afinado 35/57 (61,4 %). | Es una evaluación de imágenes OCR, no de video. Un caso sin referencia aprobada se excluyó; la revisión no tuvo doble adjudicación. |
| [`metrics/ocr_afinamiento.json`](metrics/ocr_afinamiento.json) | Compara OCR base y afinado en 86 imágenes de test. | El EMR fue 94,2 % para ambos; el archivo indica `adoptar: false`. No presentar el modelo afinado como mejora comprobada. |

La mayoría de los reportes agregados no incluye matrículas ni imágenes. Hay dos excepciones publicadas intencionalmente como materiales del proyecto: la lista de demostración/evaluación [`data/authorized_plates.csv`](../data/authorized_plates.csv) y la **referencia final del video** [`blind_eval/video_ground_truth.csv`](../blind_eval/video_ground_truth.csv) (20 pasadas, columnas `plate_gt,frame_start,frame_end`). Los CSV provisionales de `blind_eval/` (18 puntos y borrador de intervalos) son históricos. Los archivos operativos privados y las predicciones adicionales identificables no deben agregarse a los reportes públicos sin revisión.

## Evaluaciones de video e imágenes de garita

| Artefacto | Resultado o propósito | Alcance y limitación |
|---|---|---|
| [`metrics/e2e.json`](metrics/e2e.json) | Resumen general de evaluación y latencia promedio (99,21 ms); EMR y CER están en `null`. | No contiene las métricas de la corrida 7.2 por intervalos; consulta el informe final específico. |
| [`metrics/video_e2e_muestra.json`](metrics/video_e2e_muestra.json) | Evaluación E2E de cinco clips: 3/5 coincidencias exactas (60 %). | Aplicó la regla de misma placa en dos cuadros aceptados con OCR ≥0,94 dentro de 7,5 s. No hubo comparación de un solo cuadro para medir el efecto aislado; no sustituye la evaluación integral del video operativo. |
| [`metrics/video_e2e_puntos_provisionales_20261101.json`](metrics/video_e2e_puntos_provisionales_20261101.json) y [reporte](metrics/video_e2e_puntos_provisionales_20261101.md) | Informe histórico de la evaluación puntual: 11/18 exactas (61,1 %) y 9/16 recuperadas. | Usó una referencia puntual anterior; no representa los resultados de la corrida final por intervalos. La cifra 7/52 se retiró por error de cálculo. |\n| [`metrics/video_e2e_intervalos_final.json`](metrics/video_e2e_intervalos_final.json) y [reporte](metrics/video_e2e_intervalos_final.md) | Corrida final 6.9/7.2: EMR 17/24 (70,83 %), recall de placas únicas 15/17 (88,24 %), 0 falsas autorizaciones entre las 24 lecturas con referencia. | De 34 lecturas, 10 quedaron sin referencia y no se clasifican; la tasa integral de falsas autorizaciones no es estimable. La referencia contiene 20 pasadas y excluye dos dudosas. |
| [`metrics/garita_imagenes_e2e_20261101.md`](metrics/garita_imagenes_e2e_20261101.md) | Sección 7.3: 21 imágenes, detección 19/21, EMR 8/21 (38,1 %) y latencia media 37,69 ms. | Prueba por imagen; EMR por debajo de la meta del 80 %. La lista autorizada estaba vacía, por lo que cero falsas autorizaciones no demuestra su comportamiento con una lista poblada. |

La referencia final del video es [`blind_eval/video_ground_truth.csv`](../blind_eval/video_ground_truth.csv), con 20 pasadas. R1 se anotó con Claude; R2 fue una anotación ciega humana del usuario, según indicó. La adjudicación posterior conocía las lecturas previas y no fue ciega; no hubo tercera revisión humana independiente. El resultado ya ejecutado de 7.2 se resume en [`metrics/video_e2e_intervalos_final.md`](metrics/video_e2e_intervalos_final.md).

## Optimización y estabilidad multisemilla del detector

| Artefacto | Contenido |
|---|---|
| [`metrics/optimizacion_trials.csv`](metrics/optimizacion_trials.csv) | Hiperparámetros y métricas de validación de los 24 trials de Optuna. |
| [`metrics/optimizacion_importancia.csv`](metrics/optimizacion_importancia.csv) | Importancia de hiperparámetros por fANOVA y permutación. |
| [`metrics/optimizacion_antes_despues.csv`](metrics/optimizacion_antes_despues.csv) y [`metrics/optimizacion_resumen.json`](metrics/optimizacion_resumen.json) | Configuración seleccionada y comparación experimental base/optimizada en test; no implica que los pesos optimizados estén desplegados. |
| [`metrics/validacion_multisemilla_comparacion.csv`](metrics/validacion_multisemilla_comparacion.csv), [resumen](metrics/validacion_multisemilla_resumen.json), [protocolo](metrics/validacion_multisemilla_protocolo.json) y [resultados individuales](metrics/validacion_multisemilla_individuales/) | Seis entrenamientos en tres pares de semillas. La mejora media de mAP50:95 es descriptiva; tres semillas no demuestran significación estadística ni mejora punta a punta. |

Los pesos de experimentos y optimización no reemplazan automáticamente el modelo publicado. El detalle y las limitaciones están en [`docs/validacion_savh_multisemilla.md`](../docs/validacion_savh_multisemilla.md).

## Ejecución y conservación de resultados

El notebook actualizado lee los insumos versionados desde GitHub y no requiere Google Drive para iniciar. Las salidas nuevas de Colab se guardan en `/content/SIRAP_workspace` y no se publican automáticamente. Conserva en el repositorio métricas agregadas, tablas y gráficos pequeños; distribuye el video fuente como artefacto separado y no lo incrustes en el notebook. La referencia final del video es `blind_eval/video_ground_truth.csv`; el archivo de 18 puntos se conserva solo como histórico. Antes de publicar nuevas predicciones, anotaciones detalladas o registros operativos, confirma su alcance, procedencia y autorización.

Si un resultado está pendiente o su referencia es incompleta, indícalo como tal; no extrapoles métricas ni completes etiquetas por intuición.

## Aplicación, repositorio y videos

- [Aplicación SIRAP](https://eduardoceballos-sirap.hf.space) · [Hugging Face Space](https://huggingface.co/spaces/eduardoceballos/SIRAP)
- [Repositorio SIRAP_2](https://github.com/eduardoceballos666/SIRAP_2) · [API interactiva](https://eduardoceballos-sirap.hf.space/docs)
- La interfaz está disponible en español e inglés. Los videos de presentación y preguntas están enlazados al final del [README principal](../README.md).
