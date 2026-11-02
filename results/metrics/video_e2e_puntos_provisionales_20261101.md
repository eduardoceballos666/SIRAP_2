# Resultado histórico de la evaluación puntual del video

Esta corrida de la sección 7.2 usó una versión anterior de la referencia, con 18 cuadros puntuales. **Esa referencia ya no está vigente.** La referencia final es [`blind_eval/video_ground_truth.csv`](../../blind_eval/video_ground_truth.csv): 20 pasadas con intervalos inclusivos y columnas `plate_gt,frame_start,frame_end`, armada con dos anotaciones ciegas del video completo y adjudicada en el video. Los archivos de 18 puntos y el borrador de intervalos se conservan solo como históricos; ver [la revisión de la referencia final](../../blind_eval/video_ground_truth_review.md).

| Métrica histórica (18 puntos, antes del cotejo) | Resultado |
|---|---:|
| Cuadros de referencia | 18 |
| Placas distintas en la referencia | 16 |
| Lecturas emitidas por el pipeline | 52 |
| Lecturas comparadas en los cuadros anotados | 18 |
| Coincidencia exacta (EMR por lectura) | 11/18 (61,1 %) |
| Recall de placas únicas en los puntos | 9/16 (56,25 %) |
| Falsas autorizaciones | No estimables |
| Cálculo anterior retirado | 7/52; inválido porque incluyó lecturas sin referencia |
| Lecturas fuera de los cuadros de referencia | 34 |
| Cuadros procesados | 18.115 |

**Estos valores son históricos y no describen la referencia final.** El repositorio no conserva el registro por lectura de esa corrida; por eso no se pueden recalcular a partir de este resumen agregado. Para obtener métricas actuales, ejecuta 6.9 y luego 7.2 en Colab: la sección 0 carga la referencia final `blind_eval/video_ground_truth.csv`. Usa la lista autorizada que se quiera evaluar.

## Alcance y límites

- La referencia de esta corrida estaba compuesta por cuadros puntuales; no cubría intervalos completos ni todas las pasadas del video. Los valores históricos no son una evaluación integral ni recall de todos los vehículos.
- Las lecturas sin una etiqueta asociada no se clasifican como aciertos o errores.
- El cotejo visual posterior conocía lecturas anteriores, así que no constituye una segunda revisión ciega ni independiente.
- La referencia final ya tiene intervalos inclusivos por pasada sobre el video completo. Falta la nueva corrida de 6.9 y 7.2 con el mismo video. Esa referencia proviene de dos anotaciones hechas con Claude (IA), sin revisión humana.
