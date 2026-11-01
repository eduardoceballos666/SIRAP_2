# Validación del detector, el OCR y el sistema de video de SIRAP

## Resumen

Este documento reúne los resultados de validación por tipo de prueba y distingue entre métricas calculadas, revisiones humanas y pilotos. Las evaluaciones no son intercambiables: una métrica del detector no demuestra la precisión del OCR, y una lectura correcta en imágenes aisladas no demuestra el funcionamiento integral del video o de una barrera física.

| Área | Resultado disponible | Alcance y limitación |
|---|---|---|
| Detector YOLO11-s, comparación multisemilla | 6 entrenamientos, 3 pares de semillas | Mejora media descriptiva en mAP50:95; no es una prueba punta a punta ni cambia el modelo desplegado |
| OCR SAVH | 388/398 de coincidencia exacta (97,49 %) | Métrica offline condicionada a respuestas registradas; no es ciega y puede tener sesgo de confirmación |
| Piloto visual SAVH | 73/84 de coincidencia exacta (86,90 %) | Revisión piloto no independiente; 13 discrepancias pendientes de adjudicación |
| Video, cinco clips | 3/5 lecturas exactas (60 %) | Muestra de clips; no es evaluación del video operativo completo |
| Video, observaciones puntuales | 11/18 exactas (61,11 %) | Referencia puntual y dispersa; no cubre todos los vehículos ni intervalos completos |
| Imágenes completas de garita | 8/21 exactas (38,10 %) | Muestra pequeña; por debajo de la meta de EMR del 80 % |

## 1. Validación multisemilla del detector

Se compararon las configuraciones base y optimizada con YOLO11-s, usando AdamW, 40 épocas previstas, paciencia 10 y semillas emparejadas 0, 1 y 2. Se completaron seis entrenamientos. La prueba se mantuvo fija y se usó para reportar resultados, no para elegir parámetros.

| Semilla | mAP50:95 base | mAP50:95 optimizada | Diferencia (puntos porcentuales) | Recall base | Recall optimizada | Diferencia de recall (puntos porcentuales) |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 69,3573 % | 70,0945 % | +0,7372 | 95,0693 % | 95,0230 % | −0,0463 |
| 1 | 69,4552 % | 69,6736 % | +0,2184 | 95,1152 % | 96,0369 % | +0,9217 |
| 2 | 69,5956 % | 69,7629 % | +0,1673 | 94,9309 % | 94,9607 % | +0,0298 |

La diferencia media pareada en mAP50:95 es **+0,3743 puntos porcentuales**, con desviación estándar muestral de **0,3153 puntos porcentuales**. Las tres semillas mejoraron en mAP50:95. El cambio medio de recall es aproximadamente **+0,3017 puntos porcentuales**, aunque el recall disminuyó levemente en la semilla 0.

Las diferencias medias adicionales son +0,001593 en mAP50 (desviación estándar muestral 0,001230) y +0,001463 en precisión (desviación estándar muestral 0,004227). La precisión disminuyó en la semilla 0. Con tres semillas, estos datos describen la variación observada y no demuestran significación estadística ni una mejora uniforme en todas las métricas.

Los pesos de estas corridas son experimentales. No sustituyen `models/best_model.pt`, `models/best_model.onnx` ni el modelo desplegado en Hugging Face. La comparación histórica de una sola semilla es un experimento distinto y no debe mezclarse con este promedio.

Evidencia: [comparación por semilla](../results/metrics/validacion_multisemilla_comparacion.csv), [resumen](../results/metrics/validacion_multisemilla_resumen.json), [protocolo](../results/metrics/validacion_multisemilla_protocolo.json) y [métricas individuales](../results/metrics/validacion_multisemilla_individuales/).

## 2. Revisión de referencias y evaluación OCR SAVH

### 2.1 Estado de las referencias

La referencia original contiene 739 registros: 472 recortes legibles y 267 no legibles. La hoja de revisión agrupa 69 placas representativas y sus copias. Se registraron respuestas para los 69 grupos; una imagen, `fila_gt=398`, se excluyó por ilegibilidad. El conjunto evaluable quedó en 398 recortes legibles únicos.

También se cotejaron 330 referencias de cámara con las predicciones OCR guardadas: 312 coincidieron y 18 difirieron. En la revisión de los desacuerdos, 14 se resolvieron a favor de la sugerencia OCR, 3 a favor de la lectura de cámara y 1 se marcó ilegible. En dos grupos representativos se habían observado ambigüedades visuales (confusiones O/U y H/M).

### 2.2 Métricas offline condicionadas

Se reutilizaron predicciones OCR previamente guardadas; no se hizo una inferencia nueva ni se entrenó el modelo.

| Indicador | Resultado |
|---|---:|
| Recortes evaluables | 398 |
| Coincidencias exactas | 388/398 |
| EMR | 97,49 % |
| CER medio por imagen | 0,003649 |
| Aceptadas con umbral offline 0,94 | 362 |
| Correctas / erróneas entre las aceptadas con 0,94 | 359 / 3 |
| Enviadas a revisión con 0,94 | 36 |
| Aceptadas con umbral offline 0,99 | 346 |
| Correctas / erróneas entre las aceptadas con 0,99 | 343 / 3 |
| Enviadas a revisión con 0,99 | 52 |

**Interpretación:** el resultado de 388/398 depende de referencias cuya revisión incluyó, en algunos desacuerdos, sugerencias que ya mostraban la predicción OCR. Puede existir sesgo de confirmación; por eso la cifra no se debe describir como evaluación ciega o independiente. Los umbrales se aplicaron offline a las salidas disponibles y no prueban el funcionamiento integral del umbral del backend, la regla temporal, el seguimiento en video o una barrera física.

El archivo agregado sin matrículas está en [métricas SAVH aprobadas](../results/metrics/ocr_savh_aprobaciones_398.json). Las referencias individuales e imágenes de revisión permanecen en el material de trabajo privado.

### 2.3 Piloto visual del split de prueba

Se releyeron visualmente 84 imágenes del split de prueba, excluyendo dos identificadores que quedaron expuestos durante la preparación. El piloto obtuvo 73/84 coincidencias exactas por imagen (86,90 %), 63/74 por placa única (85,14 %) y CER medio de 2,04 %. Con confianza mínima 0,94 se aceptaron 80/84 resultados; 9 de esas 80 lecturas diferían de la referencia visual.

La relectura visual coincide con 71/84 referencias archivadas. Las 13 discrepancias requieren adjudicación. Además, no hubo una segunda persona independiente que realizara y verificara esta relectura. Se considera un piloto de control de etiquetas, no una evaluación ciega independiente cerrada. No se cambiaron las etiquetas originales ni se escogió automáticamente la salida OCR para resolver diferencias.

Evidencia agregada: [piloto visual SAVH](../results/metrics/ocr_savh_validacion_ciega_piloto.json).

## 3. Evaluaciones de video

### 3.1 Métricas operativas del video completo

La corrida operativa registró 18.115 cuadros a 1280×720. El procesamiento, incluyendo escritura de salida, tomó 409,6 segundos (61,77 cuadros por segundo). Se registraron 52 seguimientos y lecturas; no hubo seguimientos sin lectura. Se reportaron 25 placas con formato válido, 225 llamadas OCR, un promedio de 14,51 ms por cuadro para el detector y 0,45 ms para seguimiento. El tiempo promedio de detección más OCR por decisión fue 91,99 ms.

Estos son conteos y tiempos de operación, no métricas de exactitud. Sin una referencia completa e independiente por vehículo o pasada, no permiten calcular recall integral, falsos positivos integrales ni exactitud de extremo a extremo.

### 3.2 Muestra de cinco clips

Se evaluaron cinco clips con el ONNX publicado y el OCR `cct-s-v2-global-model` en CPU. El protocolo reprodujo el muestreo cada segundo, confianza OCR mínima de 0,94, confirmación de la misma placa en dos cuadros dentro de 7,5 segundos y continuación del video por 15 segundos cuando aún no había confirmación.

| Resultado | Valor |
|---|---:|
| Clips / eventos anotados | 5 |
| Lecturas confirmadas | 5/5 |
| Coincidencias exactas con la referencia visual | 3/5 (60 %) |
| Tiempo hasta confirmación, mediana | 8 s |
| Tiempo hasta confirmación, promedio | 10,6 s |

Dos clips produjeron confirmaciones incorrectas que superaron el umbral operativo. Esta muestra no reemplaza la evaluación del video operativo completo ni evalúa almacenamiento, apertura de barrera u otros componentes físicos. El archivo `video_03.z03` era solo una parte de un archivo dividido y no se pudo reproducir, por lo que se excluyó.

Evidencia: [evaluador reproducible](../scripts/evaluate_video_e2e.py) y [resumen de la muestra](../results/metrics/video_e2e_muestra.json).

### 3.3 Observaciones puntuales del video operativo

La referencia puntual disponible contiene 18 observaciones y 16 placas únicas. Se contabilizaron 52 lecturas del pipeline; 11/18 observaciones fueron exactas (61,11 %), y 9/16 placas únicas se recuperaron (56,25 %). Se registraron 7 autorizaciones incorrectas entre 52 lecturas (13,46 %). Otras 34 lecturas quedaron fuera de la referencia puntual; al ser una muestra dispersa, no se pueden clasificar automáticamente como falsos positivos.

Esta referencia no contiene intervalos completos ni garantiza que incluya todos los vehículos. Sus métricas son provisionales y no equivalen a una evaluación integral del video. Para cerrar la evaluación se necesita anotar cada pasada, con primer y último cuadro legibles, revisar las etiquetas de forma independiente y resolver discrepancias sin consultar las predicciones.

Evidencia: [revisión de referencia puntual](../blind_eval/video_ground_truth_review.md) y [resumen de la evaluación puntual](../results/metrics/video_e2e_puntos_provisionales_20261101.md).

### 3.4 Regla temporal y barrera

La regla de dos cuadros dentro de la ventana temporal se aplicó en la muestra de cinco clips como parte del criterio de confirmación de lectura. Los resultados de esa muestra indican que hubo dos confirmaciones incorrectas; por sí solos no prueban el desempeño en todos los escenarios.

Las pruebas documentadas no demuestran la operación de una barrera física. La confirmación lógica de una placa no debe presentarse como evidencia de que una barrera se abrió correctamente. Se requiere una prueba integral instrumentada que registre la decisión del sistema y la respuesta del dispositivo.

## 4. Evaluación con imágenes completas de garita

En 21 imágenes se obtuvo detección en 19/21 (90,48 %), coincidencia exacta en 8/21 (38,10 %), formato válido en 16/21 (76,19 %), latencia promedio de 37,69 ms y percentil 95 de 37,78 ms. La coincidencia exacta está por debajo de la meta documentada de 80 %.

El resultado de cero falsas autorizaciones con una lista de placas autorizadas vacía no demuestra el desempeño con una lista real poblada. Esta prueba se limita a las 21 imágenes evaluadas.

Evidencia agregada: [evaluación E2E de imágenes de garita](../results/metrics/garita_imagenes_e2e_20261101.md).

## 5. Reproducibilidad y artefactos

La comparación multisemilla se puede reproducir con [`validar_multisemilla_yolo11.py`](../scripts/validar_multisemilla_yolo11.py). Requiere GPU CUDA, Ultralytics, el archivo `data_abs.yaml` del dataset Roboflow v11 y el resumen de la configuración optimizada del trial 12. El script guarda protocolo, métricas individuales, comparación CSV, resumen JSON y pesos experimentales en la carpeta de salida; evita sobrescribir resultados y avisa si encuentra una corrida incompleta.

Los resúmenes públicos enlazados en este documento omiten matrículas e imágenes personales. Las referencias detalladas y fotografías de auditoría se mantienen en el almacenamiento privado de trabajo.

## 6. Conclusiones

- La comparación multisemilla muestra una mejora media pequeña en mAP50:95, con tres semillas; no justifica por sí sola cambiar el modelo publicado.
- El EMR SAVH de 97,49 % está condicionado a respuestas de revisión no ciega y no debe presentarse como independiente.
- El piloto visual SAVH necesita adjudicación humana independiente de las 13 discrepancias.
- Los cinco clips y las 18 observaciones puntuales son muestras; la segunda no cubre intervalos ni todos los vehículos.
- La muestra de imágenes completas de garita obtuvo 38,10 % de coincidencia exacta, por debajo de la meta del 80 %.
- Las cifras del detector, OCR, video y garita deben conservarse separadas y publicarse con su alcance y limitaciones.

## Acceso al producto y al código

- [Aplicación SIRAP](https://eduardoceballos-sirap.hf.space) · [Space en Hugging Face](https://huggingface.co/spaces/eduardoceballos/SIRAP)
- [Repositorio SIRAP_2](https://github.com/eduardoceballos666/SIRAP_2) · [API](https://eduardoceballos-sirap.hf.space/docs)
- La interfaz está disponible en español e inglés. Los videos de presentación están enlazados en el [README principal](../README.md).
