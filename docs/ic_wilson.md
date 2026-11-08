# Intervalo de confianza de Wilson en SIRAP

## Método

El intervalo score de Wilson estima una proporción binomial a partir de x éxitos en n observaciones: p̂ = x/n. Para un nivel de confianza de 95 %, se usa z ≈ 1,96. El método mantiene los límites dentro del rango de proporciones [0, 1] y suele comportarse mejor que el intervalo normal simple con muestras pequeñas o proporciones cercanas a 0 o 1. citeturn0search0

El cálculo requiere un denominador conocido y observaciones independientes. En datos de video, varios cuadros o lecturas de una misma pasada no deben contarse como ensayos independientes. CER, latencia y mAP no son proporciones binomiales y no se les aplica directamente este intervalo.

## Resultados del holdout ciego SAVH

| Evaluación | Aciertos | Proporción | IC de Wilson 95 % |
|---|---:|---:|---:|
| OCR base, coincidencia exacta | 42/57 | 73,7 % | 61,0–83,4 % |
| OCR afinado, coincidencia exacta | 35/57 | 61,4 % | 48,4–72,9 % |
| Cobertura OCR base | 56/57 | 98,2 % | 90,7–99,7 % |
| Cobertura OCR afinado | 56/57 | 98,2 % | 90,7–99,7 % |

El denominador corresponde a las 57 imágenes puntuables del holdout. Estos intervalos describen la incertidumbre de las proporciones calculadas sobre ese conjunto.

## Video de garita

No se informa un intervalo de Wilson para el resultado 18/30 del video. El cálculo requiere unidades independientes y referencia para todas las observaciones del denominador; lecturas repetidas dentro de una pasada y casos sin referencia no cumplen esas condiciones.

## Archivos de implementación

- Función y uso en evaluación: [src/evaluate.py](../src/evaluate.py).
- Métricas numéricas: [results/metrics/ocr_savh_wilson.json](../results/metrics/ocr_savh_wilson.json).
- Notebook reproducible: [notebooks/Evaluacion_IC_Wilson_y_muestreo.ipynb](../notebooks/Evaluacion_IC_Wilson_y_muestreo.ipynb).
