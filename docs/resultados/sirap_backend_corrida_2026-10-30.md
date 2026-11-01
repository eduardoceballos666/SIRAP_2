# SIRAP Backend — resultados de la corrida guardada

Corrida revisada en Colab el **1 de noviembre de 2026**. Se conservaron en el notebook únicamente las salidas compactas de resultados y los avisos de secciones omitidas; el video incrustado y las imágenes de diagnóstico grandes se retiraron de las salidas del notebook.

![Resumen de métricas](sirap_backend_resumen.png)

## Métricas principales

| Área | Métrica | Resultado | Meta / lectura |
|---|---|---:|---|
| Detección en test | mAP@0.5 | 0,972 | Cumple (≥ 0,850) |
| Detección en test | mAP@0.5:0.95 | 0,693 | — |
| Detección en test | Precisión / recall / F1 | 0,986 / 0,956 / 0,971 | — |
| Placas pequeñas | mAP@0.5:0.95 | 0,481 | Es el tamaño más difícil |
| OCR SAVH | EMR / CER | 93,7 % / 0,010 | Cumple EMR (≥ 80 %) |
| Inferencia | Latencia media / p95 | 13,0 / 15,1 ms | — |
| Entrenamiento | Épocas / duración | 40 / 0,70 h | GPU NVIDIA L4 |
| Video | Cuadros / placas leídas | 18.115 / 52 | 65,7 FPS de pipeline |
| Video | EMR por lectura (referencia disponible) | 55,6 % | No cumple ≥ 80 % |
| Video | Falsos autorizados en la referencia | 0 | Referencia limitada |

## Límites de esta corrida

- La lista `authorized_plates.csv` estaba vacía; las decisiones de acceso del video no representan una lista real de autorizaciones.
- La evaluación 7.3 con imágenes completas de la garita se omitió: no existía `garita/ground_truth.csv`. Para ejecutarla se requiere la carpeta `garita/imagenes/` y un CSV con columnas `image_path,plate_gt`.
- El modo en vivo se omitió porque no estaban configurados `CAMARA_URL` y `CAMARA_TOKEN`.
- El EMR de video se calculó con 18 filas de referencia (16 placas distintas); el resultado 55,6 % queda por debajo de la meta y no sustituye una referencia completa del video.
- Las consultas de propietarios no produjeron registros; el log guardado muestra errores de cierre del navegador (`TargetClosedError`).

## Videos y archivos pesados

El video fuente de la garita (459,3 MB) está publicado como asset del Release [`datos-garita-v1`](https://github.com/eduardoceballos666/SIRAP_2/releases/tag/datos-garita-v1); el notebook lo descarga desde GitHub. Los videos de salida YOLO anotado y vista comprimida se conservan aparte en Drive, según los enlaces de revisión de abajo.

- [Video anotado YOLO11 (65,2 MB)](https://drive.google.com/file/d/17Zn3Ceqx_nJ1lZJvQ8AxvBtd6qphjtzG/view)
- [Vista comprimida YOLO11 (41,7 MB)](https://drive.google.com/file/d/1Z7LIIIgbh4pn3y2NTDqWq-qrdGBtzRra/view)
- [Video original de la garita (459,3 MB)](https://drive.google.com/file/d/1coC-FcoUtMCmTtq6K3C2Y9z7W7SfC5XC/view)

No se incrustan estos archivos en el `.ipynb`; así se evita que vuelva a superar los 90 MB.


## Aplicación, repositorio y videos de presentación

- [Aplicación desplegada](https://eduardoceballos-sirap.hf.space) · [Hugging Face Space](https://huggingface.co/spaces/eduardoceballos/SIRAP)
- [Repositorio SIRAP_2](https://github.com/eduardoceballos666/SIRAP_2) · [API](https://eduardoceballos-sirap.hf.space/docs)
- La interfaz publicada está disponible en español e inglés. Los videos de presentación y preguntas están enlazados al final del [README](../../README.md).