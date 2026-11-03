# Resultados de `SIRAP_backend.ipynb`

Este informe organiza por tema las métricas de la corrida guardada y las evaluaciones posteriores. Se distinguen los resultados originales de las reevaluaciones con referencias corregidas o nuevas imágenes. Las métricas de detector, OCR, video y garita tienen alcances diferentes y no deben combinarse como una sola medida de exactitud.

![Resumen de métricas](sirap_backend_resumen.png)

## Resumen de resultados

| Componente | Resultado vigente | Alcance |
|---|---:|---|
| Detector en test | mAP@0.5: 0,972; mAP@0.5:0.95: 0,693; precisión/recall/F1: 0,986/0,956/0,971 | Métricas del detector; no miden el OCR ni la operación completa |
| Placas pequeñas | mAP@0.5:0.95: 0,481 | Es el tamaño más difícil en la evaluación del detector |
| OCR SAVH, corrida guardada | EMR: 93,7 %; CER: 0,010 | 399 referencias; 69 eran sugerencias sin confirmar |
| OCR SAVH, recálculo posterior | EMR: 388/398 (97,49 %); CER: 0,003649 | Offline, condicionado a respuestas no ciegas; no equivale a validación independiente |
| Video, evaluación 7.2 | Reejecución más reciente: EMR 18/30 (60 %); recall de placas únicas 16/17 (94,12 %); 2/30 falsas autorizaciones observadas entre lecturas clasificables | 51 lecturas; 30 con referencia y 21 sin clasificar. La tasa integral del video no es estimable. Dos pasadas dudosas siguen excluidas. La corrida guardada anterior (17/24) se conserva separada. [Informe](../../results/metrics/video_e2e_intervalos_final.md) |
| Imágenes completas de garita | Informe: EMR 8/21 (38,1 %), 37,69 ms; salida guardada del notebook: EMR 9/21 (42,9 %), 1,400674 s | Corridas distintas; la salida del notebook no tiene fecha/ID para ordenarlas. No combinar; ambas bajo la meta EMR de 80 % |
| Entrenamiento de la corrida guardada | 40 épocas; 0,70 h; GPU NVIDIA L4 | Duración y equipo de esa corrida |
| Video, rendimiento | 65,7 FPS reportados por el notebook | Medición de la corrida guardada; no mezclar con tiempos de otras ejecuciones |

## 1. Detector y entrenamiento

En el conjunto de test, el detector obtuvo mAP@0.5 de **0,972**, mAP@0.5:0.95 de **0,693**, precisión de **0,986**, recall de **0,956** y F1 de **0,971**. La meta documentada para mAP@0.5 es 0,850. En placas pequeñas, el mAP@0.5:0.95 fue **0,481**, lo que indica que ese tamaño presenta mayor dificultad.

La corrida guardada entrenó durante 40 épocas y aproximadamente 0,70 horas en una GPU NVIDIA L4. La latencia de inferencia registrada fue de 13,0 ms de promedio y 15,1 ms en el percentil 95. Estas cifras corresponden a la medición del notebook y no deben interpretarse como latencia completa de una decisión de acceso.

## 2. OCR en el conjunto SAVH

### Resultado de la corrida guardada

El notebook registró EMR de **93,7 %** y CER de **0,010** sobre 399 recortes. En ese conjunto, 69 etiquetas eran sugerencias sin confirmar. Por ello, el resultado es una métrica offline del conjunto disponible y no debe presentarse como una evaluación con todas las referencias verificadas. Aunque el valor numérico supera la meta de EMR del 80 %, la calidad de las etiquetas limita esa conclusión.

La fuente de esta corrida es [ocr_savh.json](../../results/metrics/ocr_savh.json).

### Recálculo posterior con respuestas registradas

Un recálculo offline posterior excluyó una imagen ilegible y usó 398 recortes evaluables. Obtuvo **388/398 coincidencias exactas (97,49 %)** y CER medio por imagen de **0,003649**. No se ejecutó una inferencia nueva.

Esta métrica está condicionada a las respuestas de revisión registradas. En algunos desacuerdos, las sugerencias OCR estaban visibles para quien revisó las etiquetas, por lo que puede existir sesgo de confirmación. No es una evaluación ciega ni independiente, y no demuestra que el modelo haya mejorado. Mantenerla separada del resultado original evita mezclar diferentes referencias y denominadores.

Con umbral offline de 0,94, se aceptaron 362 resultados: 359 exactos y 3 erróneos; 36 pasarían a revisión manual. Con umbral 0,99, se aceptaron 346: 343 exactos y 3 erróneos; 52 pasarían a revisión. Estas cifras se calcularon sobre predicciones guardadas y no prueban por sí solas el comportamiento integral del backend.

Fuente agregada: [ocr_savh_aprobaciones_398.json](../../results/metrics/ocr_savh_aprobaciones_398.json). Las matrículas, imágenes y filas individuales no se incluyen en este informe.

## 3. Video operativo y referencia del video

### Métricas de procesamiento

Una corrida operativa anterior procesó **18.115 cuadros**, registró **52 placas leídas** y reportó **65,7 FPS de pipeline**. Esos conteos y la velocidad describen solo esa ejecución y no deben confundirse con la corrida guardada anterior de 7.2, que contó 34 lecturas, ni con la reejecución posterior, que contó 51. Sin una referencia exhaustiva e independiente, las cifras operativas no permiten calcular exactitud o recall para todos los vehículos.

En otro resumen operativo se informa un rendimiento de **61,77 FPS** y un tiempo total de **409,6 segundos** que incluye la escritura de salida. Si los 18.115 cuadros corresponden a esos 409,6 segundos, el cociente da aproximadamente **44,22 FPS de extremo a extremo**. Por tanto, 61,77 FPS no representa ese tiempo total; y las fuentes disponibles tampoco especifican lo suficiente para reconciliarlo con los 65,7 FPS del notebook. Se conservan como mediciones separadas y no se promedian ni se comparan como si provinieran del mismo cronómetro. Los valores internos registrados fueron 14,51 ms por cuadro para el detector, 0,45 ms para seguimiento, 225 llamadas OCR y 91,99 ms de detección más OCR por decisión.

### Evaluación puntual histórica

La corrida resumida en este informe usó una versión anterior de la referencia de 18 cuadros. Sus resultados fueron 11/18 lecturas exactas (**61,1 %**) y 9/16 placas recuperadas (**56,25 %**). Son cifras históricas: el cotejo visual posterior corrigió etiquetas, agregó P003 y retiró el punto 7842. El CSV de 18 puntos se conserva como histórico; sus resultados no describen la corrida final por intervalos. La cifra de 7/52 falsas autorizaciones está retirada: comparó 52 lecturas aunque 34 no tenían referencia, por lo que no es válida.

La corrida guardada anterior reportó 0 falsas autorizaciones entre 24 lecturas clasificables y dejó 10 de 34 lecturas sin referencia. En una reejecución posterior de Colab, 6.9 registró 51 lecturas; 7.2 clasificó 30 y dejó 21 sin referencia. Esta reejecución obtuvo EMR 18/30 (60 %), recall de placas únicas 16/17 (94,12 %) y 2/30 falsas autorizaciones observadas entre lecturas clasificables. Son ejecuciones distintas: no se deben combinar sus denominadores. La tasa integral de falsas autorizaciones para todo el video sigue sin ser estimable. Ver el [informe de métricas](../../results/metrics/video_e2e_intervalos_final.md).

### Referencia publicada del video

La referencia publicada es [`blind_eval/video_ground_truth.csv`](../../blind_eval/video_ground_truth.csv) y es el archivo que usa la sección 7.2. Tiene las columnas `plate_gt,frame_start,frame_end` y 20 pasadas con intervalos inclusivos sobre los 18.115 cuadros del video. Reemplaza los 18 puntos provisionales y el borrador de intervalos, que quedan como históricos.

Se excluyeron dos pasadas dudosas y un fragmento sin placa visible. La reejecución más reciente y la corrida guardada anterior de 6.9/7.2 están resumidas por separado en [el informe de resultados](../../results/metrics/video_e2e_intervalos_final.md).

Fuentes: [reporte histórico de puntos provisionales](../../results/metrics/video_e2e_puntos_provisionales_20261101.md) y [revisión de la referencia final](../../blind_eval/video_ground_truth_review.md).

## 4. Evaluación punta a punta con imágenes completas de garita

La sección 7.3 **se omitió en una corrida guardada anterior** porque entonces no estaba disponible `garita/ground_truth.csv`. El repositorio ahora contiene las 21 imágenes y la referencia en `garita/imagenes/` y `garita/ground_truth.csv`.

| Métrica | Resultado |
|---|---:|
| Imágenes evaluadas | 21 |
| Imágenes con detección de placa | 19/21 (90,5 %) |
| Coincidencia exacta de placa (EMR) | 8/21 (38,1 %) |
| Salidas con formato ecuatoriano válido | 16/21 (76,2 %) |
| Latencia media por imagen | 37,69 ms |
| Latencia p95 por imagen | 37,78 ms |
| Detección media | 20,18 ms |
| Falsas autorizaciones reportadas | 0 |

La salida guardada del notebook registra otra ejecución sobre las 21 imágenes: detección 19/21, EMR 9/21 (42,9 %), formato válido 16/21, latencia media 1,400674 s por imagen, p95 1,905149 s y detección media 1,33666 s. No hay un identificador común ni fecha en esa salida que permita combinarla con la medición de este informe; se reportan por separado.

El EMR usa las 21 imágenes como denominador: la falta de detección o una transcripción distinta cuenta como error. El resultado de exactitud queda por debajo de la meta del proyecto de **80 %**. El informe de esa corrida registra una lista de autorizaciones vacía. El archivo `data/authorized_plates.csv` está poblado en el repositorio actual; por tanto, el cero reportado no prueba el comportamiento con la lista actualmente publicada.

Esta prueba cubre imágenes individuales: no evalúa seguimiento temporal ni sustituye la evaluación del video. Las imágenes y la referencia fila por fila están publicadas en el repositorio. El registro detallado de predicciones no aparece entre los archivos versionados. El [informe de evaluación por imágenes](../../results/metrics/garita_imagenes_e2e_20261101.md) distingue esta medición de la salida guardada en el notebook.

## 5. Secciones omitidas y resultados no concluyentes

- **Modo en vivo:** se omitió porque no estaban configuradas las variables `CAMARA_URL` y `CAMARA_TOKEN`. La corrida no verifica la conexión a una cámara real.
- **Autorización con lista poblada:** no queda evaluada en la prueba de garita, porque la lista de placas autorizadas estaba vacía.

## 6. Videos y archivos pesados

El notebook no incrusta los videos ni las imágenes de diagnóstico grandes, para mantener compacto el archivo `.ipynb`. El video fuente de la garita, de 459,3 MB, se publica como asset del Release [`datos-garita-v1`](https://github.com/eduardoceballos666/SIRAP_2/releases/tag/datos-garita-v1), desde donde el notebook lo descarga.

Los videos de salida se conservan en Drive mediante estos enlaces:

- [Video anotado YOLO11 (65,2 MB)](https://drive.google.com/file/d/17Zn3Ceqx_nJ1lZJvQ8AxvBtd6qphjtzG/view)
- [Vista comprimida YOLO11 (41,7 MB)](https://drive.google.com/file/d/1Z7LIIIgbh4pn3y2NTDqWq-qrdGBtzRra/view)
- [Video original de garita (459,3 MB)](https://drive.google.com/file/d/1coC-FcoUtMCmTtq6K3C2Y9z7W7SfC5XC/view)

Los enlaces de Drive requieren que el usuario tenga acceso a esos archivos. Las métricas agregadas y gráficos pequeños se conservan en el repositorio; los videos de salida no están incluidos en este archivo Markdown.

## 7. Aplicación, repositorio y presentación

- [Aplicación desplegada](https://eduardoceballos-sirap.hf.space) · [Hugging Face Space](https://huggingface.co/spaces/eduardoceballos/SIRAP)
- [Repositorio SIRAP_2](https://github.com/eduardoceballos666/SIRAP_2) · [Documentación interactiva de la API](https://eduardoceballos-sirap.hf.space/docs)
- La interfaz publicada está disponible en español e inglés. Los videos de presentación y preguntas están enlazados al final del [README principal](../../README.md).
