# Resultado provisional de puntos de referencia del video

Fecha de la corrida: 2026-11-01. Notebook fuente: [`notebooks/SIRAP_backend.ipynb`](../../notebooks/SIRAP_backend.ipynb), sección 7.2.

Se volvió a ejecutar 7.2 con la referencia de 18 cuadros puntuales. Las etiquetas corregidas fueron verificadas visualmente en el video original de Drive: cuadro 208 `LBA-7763` y cuadro 660 `GBR-5172`. La referencia con los 18 puntos se conserva en [`blind_eval/video_ground_truth_points_provisional.csv`](../../blind_eval/video_ground_truth_points_provisional.csv), claramente identificada como provisional.

| Métrica | Resultado |
|---|---:|
| Cuadros de referencia | 18 |
| Placas distintas en la referencia | 16 |
| Lecturas emitidas por el pipeline | 52 |
| Lecturas comparadas en los cuadros anotados | 18 |
| Coincidencia exacta (EMR por lectura) | 11/18 (61,1 %) |
| Recall de placas únicas en los puntos | 9/16 (56,25 %) |
| Falsas autorizaciones válidas | No estimables con el registro publicado |
| Cálculo anterior retirado | 7/52; inválido porque incluyó lecturas sin referencia |
| Lecturas fuera de los cuadros de referencia | 34 |
| Cuadros procesados | 18.115 |

## Alcance y límites

- Las 18 referencias son puntos (`frame_start == frame_end`), no intervalos completos ni un censo de pasadas. Estos valores no son una evaluación integral del video ni recall de todos los vehículos.
- Las 34 lecturas restantes no coinciden con una fila de referencia y no se pueden clasificar. El cálculo anterior de 7 falsas autorizaciones se retiró porque la función de 7.2 comparaba también esas filas sin etiqueta contra ground truth; no se conserva el registro por lectura para recalcular el numerador. La métrica queda no estimable hasta regenerar el registro con la lógica corregida y la misma lista autorizada.
- Los resultados son métricas condicionadas a los puntos revisados. La revisión humana independiente y la anotación completa por pasada siguen pendientes.
- El archivo CSV publicado contiene las etiquetas de esos 18 puntos y puede consultarse para reproducir la evaluación puntual. No debe tratarse como respuesta final para futuras pruebas ciegas.
- Para completar la evaluación, hay que anotar intervalos inclusivos para cada pasada, incluir vehículos omitidos por el detector, validar independientemente las placas/límites y volver a ejecutar la sección 7.2 con el mismo video.
