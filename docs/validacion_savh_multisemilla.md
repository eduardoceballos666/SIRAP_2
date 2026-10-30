# Validación: referencias SAVH pendientes y experimento multisemilla completado (30/10/2026)

**Actualización de cierre de etiquetas (30/10/2026):** se registraron respuestas para los 69 grupos SAVH y las 330 referencias de cámara; `fila_gt=398` está **marcada `ilegible`** y excluida. El EMR offline condicionado a estas respuestas es **388/398 = 97,49 %**. Los apartados 1–7 documentan etapas anteriores y sus estados pendientes son históricos. Véase el apartado 8 y [las métricas registradas](../results/metrics/ocr_savh_aprobaciones_398.json). **No equivale a una evaluación ciega ni punta a punta.**

> **Estado: validación multisemilla completada; piloto visual ciego ejecutado pero no suficiente para cierre; evaluación E2E en cinco clips completada (3/5 exactas). La revisión humana independiente y la evaluación del video operativo con referencia siguen pendientes. No atribuir al modelo publicado una mejora no desplegada.**
> Los archivos de este procedimiento no reemplazan `models/best_model.pt`, `models/best_model.onnx`,
> `config/config.yaml` ni el Space en Hugging Face.

## 1. Evidencia revisada

- Hoja conectada: **Revisión placas SAVH (142 legibles)**, accesible en Google Drive.
- La columna `revision: ok o placa correcta` tenía **142/142 celdas vacías** al leerla el 30/10/2026.
- La hoja contiene **69 grupos representativos**, con **73 copias** señaladas por `igual_a`.
- `results/metrics/ocr_savh.json` registra **399 imágenes legibles únicas** y **69 referencias sugeridas sin confirmar**. Las otras 330 no son necesariamente todas etiquetas revisadas por una persona: el estado `camara_formato_valido` es distinto de `confirmada`.
- `results/metrics/optimizacion_resumen.json` registra mAP@0.5:0.95 test **0,692586 (base)** y **0,703834 (trial 12)** con **una sola semilla**. Diferencia preliminar **+0,011248**. Los pesos optimizados NO están desplegados.

Los conteos de la hoja deben revisarse de nuevo antes del informe final. Se localizó `savh_ground_truth_subset.zip` en la carpeta privada principal `proyecto_integrador_placas` de Drive. Para la auditoría asistida más reciente se emplearon las fotografías de `revision_visual_savh/placa_legible` y las predicciones OCR ya guardadas; no debe sustituirse automáticamente un subconjunto o sus índices por imágenes distintas.

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


## 6. Auditoría visual asistida de SAVH y recálculo OCR provisional (30/10/2026)

**Estado: NO es validación definitiva de las 69 etiquetas.** Se localizaron las fotografías originales de la carpeta privada `MyDrive/proyecto_integrador_placas/revision_visual_savh/placa_legible` y se inspeccionaron las 69 imágenes representativas de la hoja **Revisión placas SAVH (142 legibles)**. La auditoría asistida encontró 67 grupos cuyas sugerencias son visualmente compatibles con los recortes, y **2 grupos ambiguos**: `n=7` (O/U; 3 recortes idénticos) y `n=52` (H/M; 1 recorte). La hoja contiene 73 filas marcadas como copias: 71 asociadas a grupos visualmente consistentes y 2 asociadas al grupo ambiguo 7. **No se rellenó la columna `revision: ok o placa correcta`**, que sigue sin aprobaciones humanas. Las columnas auxiliares K:M documentan la evaluación asistida y los grupos; no constituyen validación humana.

La referencia original contiene 739 registros (472 recortes legibles, 267 no legibles). Los 142 registros de la hoja se cruzaron con el CSV de referencia y las fotografías. La referencia corregida original en Drive se preservó sin sobrescribir. Para la reevaluación provisional se generó una copia trazable de las 739 filas y otra de **397 imágenes legibles únicas**, excluyendo únicamente las **2 imágenes únicas ambiguas** (que en la hoja corresponden a 4 filas), sin imputar ninguna letra incierta. Las otras **330 referencias** proceden de etiquetas de la cámara con formato válido; posteriormente se cotejaron las 330 con predicciones OCR y se inspeccionaron visualmente sus 18 discrepancias (sección 7), pero las 312 coincidencias y el conjunto completo no cuentan con aprobación humana.

### Cálculo reproducido con salidas OCR existentes

Se reutilizaron las 666 predicciones conservadas de `fast-plate-ocr cct-s-v2-global-model`, sin una nueva inferencia. El cálculo offline aplica la normalización del notebook y comparación exacta con las referencias de cada recorte único.

| Indicador | Histórico (399) | Revisión asistida excluyendo ambigüedades (397) |
|---|---:|---:|
| Imágenes legibles únicas | 399 | 397 |
| Lecturas exactamente correctas | 374 | 373 |
| EMR | 93,7343 % | **93,9547 %** |
| CER medio por imagen | 0,010204 | 0,009896 |
| Aceptadas con umbral offline 94 % | 363 | 362 |
| Correctas entre aceptadas con 94 % | 349 | 348 |
| Erróneas entre aceptadas con 94 % | 14 | **14** |
| Enviadas a verificación con 94 % | 36 | 35 |
| Aceptadas con umbral offline 99 % | 347 | 346 |
| Erróneas entre aceptadas con 99 % | 12 | 12 |

**Interpretación obligatoria:** el cambio de 399 a 397 modifica el denominador; no es una mejora del modelo OCR, ni constituye validación punta a punta. Un umbral de confianza offline no verifica el umbral realmente aplicado por el backend, la regla de dos cuadros, el seguimiento en video o la apertura de barrera. Tampoco confirma todas las referencias originales de la cámara.

**Archivos de evidencia privados**, sin publicar números de matrícula en GitHub:
`ocr/SIRAP2_auditoria_visual_OCR_397.xlsx`,
`ocr/SAVH_ground_truth_revision_asistida_739.csv`,
`ocr/SAVH_ground_truth_evaluable_397.csv`,
`ocr/SAVH_metricas_OCR_revision_asistida_397.json` y
`ocr/SAVH_dos_placas_por_confirmar.png` y
`ocr/SAVH_pendientes_revision_4_imagenes.csv`.
Los archivos se encuentran en el Drive privado de `proyecto_integrador_placas`; el resumen público agregado y su trazabilidad se guardan en [resultados OCR de la revisión asistida](../results/metrics/ocr_savh_revision_asistida_397.json). Se preservan los resultados históricos y las seis corridas multisemilla sin cambios.

**Para cerrar SAVH:** confirmar visualmente las 69 referencias con aprobación humana explícita (especialmente 7 y 52), registrar `ok`, placa corregida o `ilegible` en la columna J; después ejecutar nuevamente las secciones 2.2, 4.3 y 5.4 de `SIRAP_backend.ipynb`, verificar los conteos, recalcular las métricas definitivas y actualizar los resultados publicados con su nuevo estado y evidencia. Hasta ese momento, **SAVH sigue pendiente de cierre**.


## 7. Contraste adicional de referencias de cámara frente al OCR (30/10/2026)

La auditoría anterior se amplió a las **330 imágenes legibles únicas** etiquetadas originalmente como `camara_formato_valido`. Se compararon sus textos de cámara con las 330 predicciones guardadas de `fast-plate-ocr cct-s-v2-global-model`, aplicando normalización por posición. **312 coinciden y 18 difieren**. La concordancia entre cámara y OCR **no demuestra verdad terreno**, pues pueden compartir errores o confusiones sistemáticas.

Se abrieron y examinaron los 18 recortes originales discrepantes. La valoración **visual preliminar asistida** sugiere OCR en 14 casos, cámara en 3 y es incierta en 1. Estos números son clasificaciones de revisión para priorizar la comprobación y **no son confirmaciones humanas**. También siguen pendientes los dos grupos ambiguos anteriores (`n=7`, `n=52`) y la aprobación de las otras 67 sugerencias representativas. El archivo original de 739 referencias y los resultados publicados `ocr_savh.json` permanecen intactos.

Se añadió una pestaña **Auditoria camara OCR** a la misma hoja de Google Sheets: registra los 330 casos (18 discrepancias primero), comparaciones, confianza, observaciones y una columna de **aprobación humana vacía**. La pestaña **Untitled** conserva la columna J de aprobación humana sin modificar. Se guardaron de forma privada en `MyDrive/proyecto_integrador_placas/ocr/`: `SAVH_revision_330_ocr_vs_camara.csv`, `SAVH_18_desacuerdos_por_confirmar.csv`, `SAVH_auditoria_330_resumen_privado.json`, y tres láminas `SAVH_desacuerdos_{1,2,3}.png`. No se publican matrículas ni imágenes en GitHub.

El **EMR 373/397 = 93,95 % permanece provisional** y ahora tiene un riesgo adicional de etiquetas de cámara potencialmente incorrectas. No se recalcula ni se publica una nueva puntuación «corregida» escogiendo automáticamente las coincidencias con el OCR: eso produciría un sesgo circular a favor del modelo evaluado. Primero hay que aprobar o descartar visualmente los 18 desacuerdos y los grupos 7 y 52, y después revisar las referencias de cámara restantes con un protocolo independiente del OCR.

**Estado de cierre:** 0 aprobaciones humanas en las dos pestañas. Se requiere una revisión humana documentada y luego regenerar un ground truth independiente y evaluar de nuevo. El informe de detector multisemilla y los pesos de producción no cambiaron.


## 8. Cierre de respuestas registradas en SAVH y recalculo offline (30/10/2026)

**Verificación de la hoja conectada:** la pestaña `Untitled` tiene 141 respuestas `ok` entre 142 filas, pero **69/69 grupos** están cubiertos porque el grupo `n=20` tiene respuestas en las copias `n=21` y `n=22`. La pestaña `Auditoria camara OCR` tiene **329 respuestas `ok` y 1 `ilegible`**, correspondiente a `fila_gt=398`. No hay casos restantes sin una decisión de grupo o exclusión.

La fotografía `fila_gt=398` no permite leer con seguridad su último carácter. Su respuesta anterior `ok` era ambigua; el revisor cambió explícitamente el valor a **`ilegible`**, y se verificó la actualización en la fuente. La referencia queda **`excluida_por_revisor`**, sin placa imputada. La pestaña de cámara actualizó su estado a «EXCLUIDA POR ILEGIBILIDAD»; el resto indica «APROBACIÓN REGISTRADA (OK)». La pestaña SAVH incluye el estado del grupo, sin modificar las respuestas originales.

### Resultado condicionado a las aprobaciones

Con el caché OCR original se reproducen los resultados históricos `374/399 = 93,73 %`. La referencia elaborada con las respuestas registradas deja **398 recortes legibles únicos evaluables** y una exclusión. La evaluación recalculada produce **388/398 = 97,49 % de coincidencia exacta** y CER medio por imagen **0,003649**. Con umbral offline **0,94** se aceptaron 362 resultados: **359 correctos y 3 erróneos**, y 36 pasarían a revisión. Con umbral offline **0,99** se aceptarían 346: **343 correctos y 3 erróneos**, y 52 pasarían a revisión.

**Advertencia fundamental sobre las métricas:** en parte de las 18 discrepancias cámara/OCR, el revisor confirmó sugerencias que ya incluían la predicción del OCR. Por ello, el aumento numérico del EMR puede contener **sesgo de confirmación** y no es prueba de mejora real del OCR. Se trata de una **validación condicionada a aprobaciones registradas, no ciega**, sin nueva inferencia ni entrenamiento. No mide detección, seguimiento, estabilidad entre dos cuadros, latencia final ni apertura de barrera.

**Evidencia privada en Drive:** `ocr/SAVH_ground_truth_cerrado_739.csv` (las 739 filas y estados, una excluida), `ocr/SAVH_ground_truth_evaluable_398.csv`, `ocr/SAVH_resultado_ocr_398_referencias_aprobadas.csv` y `ocr/SAVH_metricas_aprobaciones_398_cerrado.json`. El resumen **agregado**, sin placas ni fotos, está en [`results/metrics/ocr_savh_aprobaciones_398.json`](../results/metrics/ocr_savh_aprobaciones_398.json). Los archivos históricos `ocr_savh.json` y `ocr_savh_revision_asistida_397.json` no se sobrescriben. El despliegue y los pesos publicados permanecen sin cambios.

**Estado actual:** decisiones de etiquetas **registradas y aplicadas**, una imagen **excluida por ilegibilidad**, recálculo offline terminado; **validación ciega independiente y evaluación real punta a punta en video todavía pendientes**.


## 9. Piloto ciego SAVH y evaluación E2E con clips de prueba (30/10/2026)

### 9.1 Relectura visual ciega del split test de OCR

Se preparó una pasada visual sin mostrar al anotador las predicciones del OCR. De las 86 imágenes del split `test` de `evidence/savh/ocr/afinamiento/particion.csv`, se releyeron 84; se excluyeron antes de anotar dos cuyos identificadores con placa quedaron visibles durante la preparación. Las referencias visuales se congelaron antes de ejecutar el modelo `cct-s-v2-global-model` de la aplicación. No se modificó el ground truth original.

Resultados **provisionales** de las 84 imágenes: EMR por imagen **73/84 = 86,90 %**, EMR por placa única **63/74 = 85,14 %**, CER medio **2,04 %**; con confianza mínima 0,94 se aceptaron 80/84 (**95,24 % de cobertura**) y 9 de esas 80 lecturas fueron distintas de la referencia visual.

La relectura visual coincide con 71/84 (**84,52 %**) de las referencias archivadas. Las 13 diferencias requieren adjudicación. Además, esta pasada la realizó el asistente visual y no una segunda persona independiente. Por estas dos razones, se registra como **piloto de control de etiquetas**, no como validación ciega independiente cerrada. No se sustituyen las métricas publicadas ni se actualizan las etiquetas por escoger la salida del OCR. Hace falta que una persona independiente revise, sin ver las predicciones, las 13 discrepancias y confirme las etiquetas antes de recalcular. El resumen agregado, sin placas, está en [métricas del piloto ciego](../results/metrics/ocr_savh_validacion_ciega_piloto.json); las anotaciones individuales se conservan fuera del repositorio público.

### 9.2 Evaluación punta a punta de lectura en video

Se procesaron cinco MP4 disponibles en `Videos_Imagenes_Prueba/` con los pesos `models/best_model.onnx` y el OCR activo `cct-s-v2-global-model` (CPU). Se anotó visualmente el vehículo principal de cada clip antes de inferir. El evaluador reproduce la lógica de la interfaz: muestreo cada 1 s, confianza OCR ≥0,94, dos cuadros con la misma placa dentro de 7,5 s y repetición del video durante 15 s después del final si todavía no hay confirmación.

| Resultado | Valor |
|---|---:|
| Clips / eventos anotados | 5 |
| Lecturas confirmadas en dos cuadros | 5/5 |
| Coincidencias exactas con la referencia visual | **3/5 (60 %)** |
| Tiempo hasta la confirmación, mediana de la línea de tiempo del video | 8 s |
| Tiempo hasta la confirmación, promedio | 10,6 s |

En dos clips el sistema confirmó una lectura incorrecta; ambas superaron el umbral operativo. No se publican las placas. El tercer archivo `video_03.z03` es solo una parte de un archivo dividido, no un video reproducible, y se excluyó. Estos cinco clips no sustituyen el video operativo `video_camiones.mp4`: este último y una referencia anotada por evento no estaban disponibles en el repositorio ni en Drive al ejecutar la evaluación. Por ello, el resultado es una medición reproducible de clips de prueba, no una validación del video operativo. Tampoco mide el registro en almacenamiento ni el accionamiento de una barrera física.

El script reproducible es [`scripts/evaluate_video_e2e.py`](../scripts/evaluate_video_e2e.py); el resumen sin placas y los hashes de los archivos probados están en [video_e2e_muestra.json](../results/metrics/video_e2e_muestra.json). La tabla privada de referencias `video_path,plate_gt` no se publica.

**Estado de las dos tareas:** la lectura de video ya tiene una evaluación de cinco clips, con dos errores de aceptación que deben corregirse antes de adoptar cambios; falta evaluar el video operativo con su ground truth. La validación ciega independiente queda pendiente hasta adjudicar las 13 discrepancias mediante un revisor humano independiente.
