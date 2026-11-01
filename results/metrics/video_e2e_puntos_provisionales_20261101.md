# Resultado histórico de la evaluación puntual del video

Esta corrida de la sección 7.2 usó una versión anterior de la referencia, con 18 cuadros puntuales. Después de una revisión visual posterior se corrigieron cuatro etiquetas, se retiró el punto 7842 por falta de sustento visual y se excluyeron dos puntos PZF que siguen sin resolverse. La referencia pública actual contiene 15 puntos exactos provisionales.

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

**Estos valores son históricos y no describen la referencia corregida de 15 puntos.** El repositorio no conserva el registro por lectura de esa corrida; por eso no se pueden recalcular a partir de este resumen agregado. Para obtener métricas actuales, corre 6.9 y luego 7.2 en Colab con la referencia corregida y la lista autorizada que se quiera evaluar.

## Alcance y límites

- La referencia actual sigue compuesta por cuadros puntuales; no cubre intervalos completos ni todas las pasadas del video. Los valores históricos no son una evaluación integral ni recall de todos los vehículos.
- Las lecturas sin una etiqueta asociada no se clasifican como aciertos o errores.
- El cotejo manual posterior conocía las lecturas anteriores, así que no constituye una segunda revisión ciega ni independiente.
- La evaluación integral requiere intervalos inclusivos por pasada, los vehículos omitidos por el detector, validación independiente de las placas y límites y una nueva corrida con el mismo video.
