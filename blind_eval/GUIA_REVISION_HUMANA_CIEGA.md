# Protocolo de revisión humana ciega e independiente

## Objetivo

Obtener una referencia visual humana independiente para medir OCR sin que quien etiqueta conozca las predicciones del sistema. La revisión debe preceder al cotejo con las predicciones.

## Preparación de la revisión

1. Una persona coordinadora que no etiqueta prepara imágenes nuevas o un subconjunto reservado, verifica que no se haya usado para entrenar o ajustar el modelo y asigna identificadores aleatorios (blind_id).
2. Entrega al revisor únicamente las imágenes originales o recortes de la placa, sin texto OCR, cajas, nombres de archivo que revelen etiquetas, resultados previos ni el orden de las predicciones.
3. Mantiene en privado la correspondencia entre blind_id y archivo fuente, las etiquetas de referencia previas y cualquier predicción.
4. El segundo revisor transcribe lo que ve directamente en la imagen y marca si es legible. Si hay duda, registra la incertidumbre; no adivina ni copia una propuesta del OCR.

## Cierre y discrepancias

1. Guarda la primera anotación del revisor sin modificarla y con fecha/identificador del revisor.
2. Solo después de congelar esa anotación, una persona autorizada coteja las dos revisiones.
3. Registra cada discrepancia y su resolución mediante una tercera lectura visual independiente o adjudicación humana documentada. No resuelvas una discrepancia eligiendo automáticamente la predicción OCR.
4. Congela la referencia adjudicada antes de revelar y puntuar las predicciones.
5. Para reportar resultados, publica protocolo, tamaño de muestra, reglas de exclusión, métricas agregadas y resumen de discrepancias. No publiques claves de respuesta, matrículas por fila, predicciones por fila ni la correspondencia de identificadores.

## Subconjuntos futuros

Las etiquetas SAVH y las particiones que ya están publicadas en este repositorio no constituyen una clave secreta para futuras pruebas ciegas. Para una evaluación futura estrictamente ciega, selecciona imágenes nuevas o un subconjunto cuyas etiquetas y correspondencias se mantengan privadas hasta congelar predicciones y anotaciones.

## Formato privado de trabajo

La plantilla vacía revision_humana_template.csv sirve para la primera transcripción. Debe guardarse en una ubicación privada; no subas al repositorio sus filas rellenadas. Para video, consulta también GUIA_ANOTACION_VIDEO.md: cada fila de video representa una pasada y un intervalo de cuadros legibles, y hace falta revisar los vehículos que el detector pudo omitir. La referencia final del video ya está publicada en `video_ground_truth.csv`.
