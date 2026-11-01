# Resultados

| Carpeta | Contenido |
|---|---|
| `figures/` | Gráficos pequeños del notebook para el informe y los documentos (`docs/`). |
| `metrics/` | Métricas JSON/CSV y resúmenes agregados del proyecto. |
| `reports/` | Reportes generados; los logs locales se ignoran con Git. |

## Resultados publicados

| Archivo | Origen | Alcance |
|---|---|---|
| `metrics/detector_test.json` | Sección 5.1 | mAP, precisión, recall y F1 del detector. |
| `metrics/umbrales.json` | Sección 4.1 | Umbrales calibrados en validación. |
| `metrics/ocr_savh.json` | Secciones 4.3 y 5.4 | EMR, CER y tamaño de muestra OCR SAVH. |
| `metrics/e2e.json` | Sección 7 | Evaluación puntual de imagen; no sustituye la evaluación de video. |
| `metrics/video_e2e_puntos_provisionales_20261101.md` y `.json` | Sección 7.2 | Resultados agregados de 18 cuadros puntuales corregidos; provisionales, no cubren todos los intervalos ni vehículos. |
| `metrics/garita_imagenes_e2e_20261101.md` | Sección 7.3 | Métricas agregadas de 21 imágenes de garita. |
| `metrics/velocidad.json` | Sección 5.3 | Latencia, FPS, parámetros y GFLOPs. |
| `metrics/optimizacion_trials.csv` | `notebooks/04_optimizacion.ipynb` | Hiperparámetros y métricas de validación de 24 trials. |
| `metrics/optimizacion_importancia.csv` | `notebooks/04_optimizacion.ipynb` | Importancia fANOVA y permutación. |
| `metrics/optimizacion_antes_despues.csv`, `optimizacion_resumen.json` | `notebooks/04_optimizacion.ipynb` | Mejor configuración y comparación en test. |

El notebook actualizado lee insumos versionados desde GitHub y no necesita Google Drive. Sus nuevas corridas guardan primero los resultados en `/content/SIRAP_workspace` de Colab. Publica únicamente tablas, métricas agregadas y gráficos pequeños; no incrustes videos ni subas predicciones individuales. Si un resultado no está, se documenta como pendiente en vez de estimarlo.

## Umbral operativo OCR

La aplicación usa un umbral de confianza OCR de **99 %**. Las lecturas por debajo pasan a verificación manual.


## Relación con la aplicación y el repositorio

Los resultados de modelado deben leerse dentro del alcance de cada protocolo y conjunto de datos. La aplicación SIRAP 1.0 está desplegada en [Hugging Face](https://huggingface.co/spaces/eduardoceballos/SIRAP) ([abrir aplicación](https://eduardoceballos-sirap.hf.space)); el código, notebooks, métricas y documentación se mantienen en [GitHub SIRAP_2](https://github.com/eduardoceballos666/SIRAP_2). También está disponible la [API interactiva](https://eduardoceballos-sirap.hf.space/docs). La interfaz ofrece español e inglés; los videos requeridos están al final del [README principal](../README.md).