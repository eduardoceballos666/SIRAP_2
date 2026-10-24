# Optimización de hiperparámetros – SIRAP (Workshop S5)

Notebook: `notebooks/04_optimizacion.ipynb` · Resultados: `results/metrics/optimizacion_*.csv|json` ·
Figuras: `results/figures/opt_*.png`

> **Estado.** El modelo entregado usa la configuración base del preset «completo» (sección 2 de este documento).
> El estudio de sensibilidad está implementado en `04_optimizacion.ipynb` y se ejecuta en Colab con GPU; las
> tablas marcadas con ⏳ se completan con su salida (`results/metrics/optimizacion_trials.csv`). No se reportan
> números que no se hayan medido.

---

## 1. Qué se optimiza y con qué métrica

- **Modelo:** detector YOLO11-s (el OCR es un modelo preentrenado; su único «hiperparámetro» operativo es el
  umbral de confianza, que se trata en la sección 6).
- **Métrica objetivo:** mAP@0.5:0.95 en *val* (más exigente que mAP@0.5 con la localización, lo que importa para
  recortar bien la placa antes del OCR). Se reporta también mAP@0.5.
- **Presupuesto:** 24 corridas cortas (10 épocas, 30 % de *train*, 25 % de *val* para validar cada época,
  semilla fija), equivalente a ≈2–3 h de una T4. La mejor configuración se reentrena luego con el protocolo
  completo (40 épocas, 100 % de los datos) y se compara con la base **en *test***.

## 2. Configuración base (antes de optimizar)

| Hiperparámetro | Valor base |
|---|---|
| `lr0` (tasa de aprendizaje inicial) | 0,002 (AdamW automático de Ultralytics) |
| `weight_decay` | 0,0005 |
| `imgsz` | 640 |
| `batch` | 16 |
| `mosaic` | 1,0 |
| `hsv_v` (brillo) | 0,4 |
| `cos_lr` | False |
| `epochs` / `patience` | 40 / 10 |

## 3. Espacio de búsqueda

| Hiperparámetro | Rango / valores | Escala | Por qué |
|---|---|---|---|
| `lr0` | 1e-4 – 1e-2 | logarítmica | Es el hiperparámetro que más suele mover la convergencia |
| `weight_decay` | 1e-5 – 1e-3 | logarítmica | Regularización; dataset de una clase propenso a sobreajuste |
| `imgsz` | 512, 640, 768 | categórica | Placas pequeñas (17,6 % del *test*) necesitan resolución |
| `batch` | 8, 16, 32 | categórica | Ruido del gradiente (con `nbs=64` el lote efectivo es fijo) |
| `mosaic` | 0 – 1 | lineal | Aumento que crea objetos pequeños y contextos variados |
| `hsv_v` | 0 – 0,8 | lineal | Robustez a iluminación (día, noche, sombra de la garita) |
| `cos_lr` | True / False | categórica | Forma del *scheduler* |

**Método:** búsqueda **bayesiana TPE** (Optuna, 24 *trials*, 6 aleatorios iniciales). El optimizador se fija en
`AdamW` de forma explícita: con `optimizer="auto"` Ultralytics ignora `lr0` y lo recalcula, y el estudio no mediría nada. Se eligió TPE frente a *grid search* porque 7 dimensiones × 3 valores serían 2 187
combinaciones.

## 4. Análisis de sensibilidad

El notebook produce, a partir de la tabla de *trials*:

1. **Ranking de importancia** con **fANOVA** (`optuna.importance.FanovaImportanceEvaluator`): qué fracción de la
   varianza del mAP explica cada hiperparámetro. Se contrasta con la importancia por permutación de un
   *random forest* sustituto (para no depender de un solo método).
2. **Partial dependence plots (PDP)** 1D: efecto promedio de cada hiperparámetro sobre el mAP predicho por el
   sustituto, manteniendo los demás en su distribución observada.
3. **Interacciones**: PDP 2D de los dos pares más importantes según el ranking (p. ej. `lr0 × batch`,
   `imgsz × mosaic`).
4. **Curvas de sensibilidad de un factor**: variar un hiperparámetro alrededor de la mejor configuración.

### 4.1 Ranking de importancia ⏳

| # | Hiperparámetro | Importancia fANOVA | Importancia por permutación |
|---|---|---|---|
| 1 | ⏳ | ⏳ | ⏳ |
| 2 | ⏳ | ⏳ | ⏳ |
| 3 | ⏳ | ⏳ | ⏳ |

![Importancia](../results/figures/opt_importancia.png) ⏳

### 4.2 Partial dependence plots ⏳

![PDP](../results/figures/opt_pdp.png) ⏳

### 4.3 Interacciones ⏳

![Interacciones](../results/figures/opt_interacciones.png) ⏳

## 5. Configuración final y comparación antes / después

| Configuración | mAP@0.5 *test* | mAP@0.5:0.95 *test* | mAP pequeñas | Tiempo/época |
|---|---|---|---|---|
| Base (preset «completo», entregada) | 0,972 | 0,693 | 0,481 | ≈63 s (GPU L4) |
| Optimizada | ⏳ | ⏳ | ⏳ | ⏳ |

**Criterio de selección:** se adopta la configuración optimizada solo si mejora el mAP@0.5:0.95 de *test* en más
que la variación entre semillas (se reentrena con 2 semillas); si no, se conserva la base por simplicidad y se
documenta el hallazgo.

## 6. Optimización de umbrales (ya aplicada)

Además de los hiperparámetros de entrenamiento, el sistema tiene dos umbrales de operación:

| Umbral | Cómo se fija | Valor |
|---|---|---|
| Confianza del detector | Calibrado **en *val*** (sección 3 del notebook): máx. F1 para seguir (`conf_track`) y menor umbral con precisión ≥ 95 % para decidir (`conf_decision`), con piso 0,10 | **0,30** y **0,30** (F1 máx. en val = 0,967) |
| Confianza OCR para decidir sin verificación manual | Estudio de confianza del OCR en SAVH (sección 5): umbrales 0,5–0,99, máximo 15 % a verificación manual | **0,99**: 13 % a verificación manual, lecturas equivocadas aceptadas 25 → 12 (AUROC 0,76) |
| Tamaño de inferencia en video | Comparación 640 vs 1280 px en el video de la garita (sección 6) | 1280 px en video, 640 px en imágenes |

### 6.1 Efecto de la regla de decisión optimizada (SAVH, lista simulada, 399 imágenes)

| Configuración | Falsos autorizados | Rechazos indebidos | A verificación manual |
|---|---|---|---|
| Sin umbral OCR | 0 de 202 | 1 de 197 | 4,0 % |
| Umbral OCR 0,99 (adoptado) | 0 de 202 | 1 de 197 | 15,5 % |

El umbral cambia poco en esta muestra (los falsos autorizados ya eran 0), pero baja el **peor caso** estimado de
vehículos no autorizados que entrarían como autorizados de 6,3 % a 3,0 % (sección 5 del notebook): se prioriza la
seguridad a costa de más verificaciones manuales.

### 6.2 Curvas del entrenamiento base

![Entrenamiento YOLO11-s](../results/figures/entrenamiento_yolo11_completo.png)

El mAP@0.5 de validación supera la meta (0,85) desde la época 2 y el mAP@0.5:0.95 sigue subiendo hasta la época 40
(0,691): el *early stopping* (paciencia 10) no se activó, lo que sugiere que más épocas podrían aportar algo en la
métrica estricta. Es uno de los hiperparámetros a incluir en el estudio.

## 7. Lecciones

- Los cambios de arquitectura (YOLOv8 → RF-DETR → YOLOv8n → YOLO11-s) y de OCR (GLM-OCR → fast-plate-ocr) tuvieron
  más impacto en el sistema que cualquier hiperparámetro: por ejemplo, el OCR pasó de un modelo de lenguaje-visión a
  uno de 5 MB que corre en CPU sin perder exactitud en SAVH.
- La resolución de inferencia (`imgsz`) fue decisiva para las placas pequeñas del video real.

## 8. Afinamiento del OCR con placas ecuatorianas (`notebooks/06_afinamiento_ocr.ipynb`)

`cct-s-v2-global-model` no incluye Ecuador entre sus regiones, aunque ya logra 93,7 % de EMR en SAVH Guayaquil.
El notebook 06 prueba si afinarlo mejora ese resultado sin sesgar la evaluación:

| Decisión | Por qué |
|---|---|
| Separación **por placa** (60 / 15 / 25 %) | Una placa repetida en *train* y *test* inflaría el EMR |
| Solo referencias confirmadas (`INCLUDE_UNCONFIRMED = False`) | Una etiqueta sin confirmar podría enseñar un error y además premiarlo en la evaluación |
| Partir de `cct_s_v2_global.keras` (pesos publicados por el autor) | Afinar, no entrenar desde cero: pocos cientos de ejemplos |
| *lr* 3e-4, *weight decay* 5e-4, sin *label smoothing*, 40 épocas con *early stopping* (10) | Cambios pequeños sobre un modelo que ya funciona |
| Aumentos suaves (±8°, brillo, desenfoque, ruido, compresión) | La garita varía más en luz y foco que en geometría |
| Misma métrica que la app (EMR tras normalizar, CER, aceptadas con confianza ≥ 0,99) | Comparar exactamente lo que importa en producción |
| Se adopta solo si mejora el EMR con **McNemar p < 0,05** y no aumenta las lecturas equivocadas aceptadas | Con ≈100 imágenes de *test*, cada acierto vale ≈1 punto de EMR |

### 8.1 Resultados (corrida del 24/10/2026, Colab)

**Datos:** 330 recortes legibles de SAVH con referencia confirmada (las 69 sugerencias sin confirmar quedaron
fuera), 297 placas distintas, repartidas por placa en 194 / 50 / 86 imágenes (*train* / *val* / *test*).

**Entrenamiento:** partió de `cct_s_v2_global.keras`; la exactitud de placa en *val* subió de 0,969 (época 1) a
**0,984** en la época 4 y el *early stopping* lo detuvo en la época 14. El modelo original obtiene 0,960 en el mismo
*val*.

![Curvas del afinamiento](../results/figures/ocr_afinamiento_curvas.png)

**Comparación en *test* (86 imágenes de placas que el modelo no vio):**

| Modelo | EMR | IC 95 % (Wilson) | CER | Aceptadas con confianza ≥ 0,99 | Equivocadas aceptadas |
|---|---|---|---|---|---|
| Original (`cct-s-v2-global-model`) | **94,2 %** | 87,1 % – 97,5 % | 0,013 | 90,7 % | 1 |
| Afinado con placas ecuatorianas | **94,2 %** | 87,1 % – 97,5 % | 0,013 | 89,5 % | 1 |

Los dos modelos aciertan y fallan **exactamente en las mismas imágenes** (0 placas que solo uno lee bien;
McNemar *p* = 1,0).

**Decisión: se mantiene el modelo original.** La mejora que se ve en *val* (0,960 → 0,984, una o dos imágenes) no se
repite en *test*: era ajuste al conjunto usado para elegir la época. El afinado además acepta un poco menos de
lecturas sin verificación manual (89,5 % frente a 90,7 %) sin reducir los errores aceptados.

**Interpretación.**
- El modelo general ya generaliza bien a placas ecuatorianas de una fila: los errores que quedan (≈5 de 86) son
  difíciles para ambos modelos (placas borrosas o con caracteres ambiguos como O/Q), no un problema de «región».
- Con 194 imágenes de entrenamiento no hay señal suficiente para mover un modelo entrenado con más de 85 000 placas.
- Vale la pena repetir el experimento cuando haya **más y mejores datos**: la hoja de revisión confirmada
  (`INCLUDE_UNCONFIRMED = True`, +69 imágenes difíciles) y recortes reales de la garita hechos por YOLO11-s
  (sección 7 del notebook), que además permitirían medir el EMR punta a punta.

Resultados completos en `results/metrics/ocr_afinamiento.json`.
