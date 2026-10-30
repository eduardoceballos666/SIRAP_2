# Validación: referencias SAVH pendientes y experimento multisemilla completado (30/10/2026)

> **Estado: entrenamiento multisemilla completado; revisión visual SAVH pendiente. No atribuir al modelo publicado una mejora no desplegada.**
> Los archivos de este procedimiento no reemplazan `models/best_model.pt`, `models/best_model.onnx`,
> `config/config.yaml` ni el Space en Hugging Face.

## 1. Evidencia revisada

- Hoja conectada: **Revisión placas SAVH (142 legibles)**, accesible en Google Drive.
- La columna `revision: ok o placa correcta` tenía **142/142 celdas vacías** al leerla el 30/10/2026.
- La hoja contiene **69 grupos representativos**, con **73 copias** señaladas por `igual_a`.
- `results/metrics/ocr_savh.json` registra **399 imágenes legibles únicas** y **69 referencias sugeridas sin confirmar**. Las otras 330 no son necesariamente todas etiquetas revisadas por una persona: el estado `camara_formato_valido` es distinto de `confirmada`.
- `results/metrics/optimizacion_resumen.json` registra mAP@0.5:0.95 test **0,692586 (base)** y **0,703834 (trial 12)** con **una sola semilla**. Diferencia preliminar **+0,011248**. Los pesos optimizados NO están desplegados.

Los conteos de la hoja deben revisarse de nuevo antes del informe final. El subconjunto de imágenes `savh_ground_truth_subset.zip` no se encontró entre los archivos actualmente indexados en el Drive conectado; debe estar disponible en Colab para reconstruir la referencia completa. Existe el dataset de origen publicado en Zenodo, pero no sustituir automáticamente el subconjunto ni sus índices por una muestra diferente.

## 2. Auditar las etiquetas SAVH, sin inventar ninguna

En Google Colab con Drive montado:

```python
from google.colab import drive
drive.mount("/content/drive")
```

Con el repositorio disponible en `/content/SIRAP_2`, ejecutar en una celda de Colab:

```python
%run /content/SIRAP_2/scripts/auditar_savh.py --output-dir /content/drive/MyDrive/proyecto_integrador_placas/auditoria_savh
```

El script lee la hoja por Google Sheets y guarda **solo en Drive privado**:

- `auditoria_savh/savh_auditoria.json`: recuentos y conflictos;
- `auditoria_savh/savh_pendientes_revision.csv`: una fila por grupo que requiere inspección.

No publica placas en el repositorio abierto.

**La validación es visual.** En la última columna de la hoja escribir `ok` si la sugerencia coincide con la imagen, la placa corregida si difiere o `ilegible` si no puede saberse. Revisar especialmente grupos marcados `dudosa` y las confusiones O/Q/0. Una respuesta en una imagen duplicada se propaga al grupo por el notebook original. No rellenar `ok` a partir del texto sugerido, del nombre de archivo ni del resultado del OCR.

Una vez revisadas las imágenes, en `notebooks/SIRAP_backend.ipynb` ejecutar secciones **0, 1.3, 2.1 y 2.2**, y confirmar que la guía de imágenes pendientes no presente respuestas faltantes. A continuación recalcular **4.3 y 5.4**, exportar las métricas actualizadas a `results/metrics/ocr_savh.json` y actualizar la documentación. Si hay imágenes irresolubles, excluirlas de las métricas con el estado correspondiente y documentar su número.

`notebooks/06_afinamiento_ocr.ipynb` puede reutilizar las referencias corregidas con `INCLUDE_UNCONFIRMED = False`, porque el filtrado ya admite los estados confirmados. **No activar `True` para incluir sugerencias no verificadas.**

## 3. Validar la estabilidad del detector con semillas emparejadas

**Protocolo ejecutado el 30/10/2026.** No se repitieron los 24 trials de Optuna: el trabajo consistió en reentrenar de forma independiente la configuración base y el trial 12 con semillas **0, 1 y 2**, manteniendo protocolo y dataset, para totalizar **seis entrenamientos completos**.

**Ejecución verificada el 30/10/2026:** seis corridas de YOLO11-s finalizadas en Colab con Tesla T4 y tres pares documentados. Se conservan los pasos siguientes como procedimiento reproducible. La revisión visual de las 69 referencias SAVH sigue pendiente.

1. Abrir `notebooks/04_optimizacion.ipynb` en Colab y ejecutar solo las celdas iniciales de instalación, Drive y preparación del **dataset Roboflow v11** (antes de lanzar Optuna).
2. Verificar que existe `/content/datasets/license-plate-recognition-rxg4e-v11/data_abs.yaml` y que `MyDrive/proyecto_integrador_placas/optimizacion/optimizacion_resumen.json` sigue accesible.
3. Con el repositorio disponible en `/content/SIRAP_2`, ejecutar **en el runtime GPU**:

```python
%run /content/SIRAP_2/scripts/validar_multisemilla_yolo11.py --data-yaml /content/datasets/license-plate-recognition-rxg4e-v11/data_abs.yaml --opt-summary /content/drive/MyDrive/proyecto_integrador_placas/optimizacion/optimizacion_resumen.json --output-dir /content/drive/MyDrive/proyecto_integrador_placas/optimizacion/validacion_multisemilla --seeds 0 1 2
```

**Se generan** en la carpeta de salida privada:

- `protocolo.json`: parámetros, hash de `data_abs.yaml`, versiones y GPU;
- `runs/base_semilla_*/weights/best.pt` y `runs/optimizada_semilla_*/weights/best.pt` (solo experimentales);
- `metricas_individuales/*.json`;
- `comparacion_multisemilla.csv`;
- `resumen_multisemilla.json`: mejoras emparejadas, media, desviación y cantidad de semillas con ventaja.

El script evita reemplazar una corrida existente y permite reutilizar métricas ya terminadas. Si existe una corrida **incompleta**, no intenta reanudarla automáticamente ni borrar archivos: revisar manualmente checkpoints y coherencia del protocolo. El conjunto de prueba es fijo y **no se usa para seleccionar nuevos parámetros**. Tres semillas son una evaluación descriptiva, no demostración de significancia estadística.

## 4. Criterios de cierre

- Confirmación visual documentada de las 69 referencias únicas; sin respuestas incompletas/conflictivas en la hoja, o exclusión motivada de imágenes ilegibles.
- `savh_ground_truth_corregido.csv` regenerado y `ocr_savh.json` recalculado con etiquetas fiables; revisar cuántas imágenes válidas quedan después de excluir.
- **Completado (30/10/2026):** seis entrenamientos terminados, resultados de los tres pares y variabilidad documentada.
- Medir cambios en **recall** además de mAP; no adoptar una mejora de cajas que comprometa el número de placas detectadas.
- Actualizar `docs/optimizacion.md`, `docs/analisis_datos.md` y `README.md` **solo con resultados efectivos y verificables**; no copiar resultados hipotéticos.
- Conservar el modelo base de Hugging Face salvo una decisión posterior justificada por evaluación punta a punta, recalibración, exportación ONNX y pruebas integrales.

**Riesgo de interpretación:** el entrenamiento base original de SIRAP y el ensayo base controlado de Optuna pueden diferir en detalles del optimizador; la nueva comparación emparejada compara dos protocolos experimentales con `AdamW` explícito. No se debe atribuir automáticamente su promedio a los pesos ONNX que están publicados.


## Validación multisemilla terminada (30/10/2026)

Se entrenaron independientemente las configuraciones **base** y **optimizada** con AdamW, 40 épocas previstas, paciencia 10 y semillas 0, 1 y 2 (seis corridas). Es un experimento controlado distinto de la comparación histórica de una sola semilla y de los pesos publicados.

| Semilla | mAP50:95 base | mAP50:95 optimizada | Diferencia (pp) | Recall base | Recall optimizada | Diferencia recall (pp) |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 69,3573 % | 70,0945 % | +0,7372 | 95,0693 % | 95,0230 % | −0,0463 |
| 1 | 69,4552 % | 69,6736 % | +0,2184 | 95,1152 % | 96,0369 % | +0,9217 |
| 2 | 69,5956 % | 69,7629 % | +0,1673 | 94,9309 % | 94,9607 % | +0,0298 |

**Mejora media pareada en mAP50:95: +0,3743 puntos porcentuales**; desviación estándar **muestral: 0,3153 puntos porcentuales** (n=3). El recall medio pareado varía aproximadamente **+0,3017 puntos porcentuales**. Las tres semillas mejoran en mAP50:95, pero la magnitud varía y el recall baja levemente en la semilla 0. Esto describe estabilidad limitada, **no** significación estadística ni mejora punta a punta en video.

Evidencia: [comparación CSV](../results/metrics/validacion_multisemilla_comparacion.csv), [resumen JSON](../results/metrics/validacion_multisemilla_resumen.json), [protocolo JSON](../results/metrics/validacion_multisemilla_protocolo.json). La comparación anterior de una semilla permanece como resultado histórico separado. **No se reemplazan** `models/best_model.pt`, `models/best_model.onnx` ni los pesos de Hugging Face. Las **69 referencias SAVH** continúan pendientes de verificación visual; tampoco está demostrada una mejora del OCR o del sistema completo.


### Métricas complementarias de la validación multisemilla: mAP50 y precisión

| Semilla | mAP50 base | mAP50 optimizada | Δ mAP50 | Precisión base | Precisión optimizada | Δ precisión |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.973401 | 0.973779 | +0.000378 | 0.992304 | 0.988982 | -0.003322 |
| 1 | 0.970963 | 0.973800 | +0.002838 | 0.983629 | 0.986651 | +0.003022 |
| 2 | 0.970954 | 0.972518 | +0.001564 | 0.988563 | 0.993252 | +0.004689 |

Las diferencias medias pareadas son **+0.001593** en mAP50 (DE muestral **0.001230**) y **+0.001463** en precisión (DE muestral **0.004227**). El valor de precisión también disminuye en la semilla 0; la evidencia de estabilidad de las tres semillas no garantiza una mejora uniforme en todas las métricas. Los seis JSON originales, con las cuatro métricas y rutas a pesos experimentales, se conservan en [resultados individuales](../results/metrics/validacion_multisemilla_individuales/base_semilla_0.json) y los otros cinco archivos del mismo directorio.
