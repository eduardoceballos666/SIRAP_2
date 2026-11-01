# Revisión y cotejo provisional de `video_camiones.mp4`

## Alcance de la referencia puntual

La referencia pública contiene 18 cuadros seleccionados, con `frame_start == frame_end`. Sirve para medir lecturas en esos puntos; no describe los intervalos completos de legibilidad ni incluye necesariamente todas las pasadas del video. No debe presentarse como evaluación integral.

La anotación ciega original se conserva aparte como registro histórico. El cotejo que se documenta abajo se hizo después de conocer lecturas anteriores; por ello no constituye una segunda revisión ciega ni una revisión independiente. La revisión visual de P003 y PZF se hizo directamente en los cuadros del video original: 1312, 4817 y 16506.

## Cotejo visual

| Caso | Lectura observada | Disposición para la referencia |
|---|---|---|
| P001, cuadro 208 | `LBA-7763`; la forma del dígito favorece 6 frente a 8. Confianza media-alta. | Se conserva `LBA-7763`. |
| P002, cuadro 660 | `GRW-5172`; el segundo carácter es R y el tercero W. | Corregido de `GBR-5172` a `GRW-5172`. |
| P003, cuadro 1312 | La placa visible dice `POD-350`: se distinguen las letras POD y no hay cuarto dígito. | Se incorpora como `POD-0350`, aplicando la regla documentada para placas antiguas de tres dígitos. |
| P011, cuadro 5197 | `ABI-8220`; el tercer carácter no coincide con T. | Corregido de `ABT-8220` a `ABI-8220`. |
| P012, cuadro 6388 | `GBO-5174` es legible hasta el cuadro 6390 y deja de verse desde 6392. | Hallazgo de intervalo; este cuadro no forma parte de los 18 puntos seleccionados. |
| Cuadro 7842 | No aparece un vehículo; se ve el resplandor de los neblineros. `GBN-2864` había salido del video en el corte de 7322. | Punto 7842 eliminado por falta de sustento visual. |
| P014, cuadro 8408 | `GBQ-2106`; el tercer carácter tiene curva y cola, no la forma de D. | Corregido de `GBD-2106` a `GBQ-2106`. |
| P016 | `GLB-0246`; el tercer carácter tiene dos lóbulos. | Se conserva `GLB-0246`; la referencia anterior con `GLD-0246` queda marcada como errónea. |
| P017 | `GBQ-6255`; el tercer carácter es cerrado y tiene cola, no es V. | Hallazgo para el cotejo de pasadas; no se añadió un punto sin un índice de cuadro confirmado. |
| P020, cuadro 14817 | `GPQ-0783`; la Q tiene cola. El primer dígito después del guion es 0. | Corregido de `GPR-0783` a `GPQ-0783`. El 0 sirve como comparación visual para PZF. |
| P010/P022, cuadros 4817 y 16506 | `PZF-0329`; el primer carácter después del guion es visualmente un 0 y coincide con la forma del 0 de `GPQ-0783`. | Se conservan ambos puntos como `PZF-0329`. |

En P003, la imagen muestra tres dígitos después del guion. El notebook normaliza una placa antigua de tres dígitos agregando un cero a la izquierda, por lo que el valor de referencia normalizado es `POD-0350`. En PZF, la lectura se basa en los cuadros del video y la comparación con `GPQ-0783`; el formato de placa por sí solo no se usó para escoger el carácter.

La anotadora señaló una inconsistencia propia: no había marcado como dudoso el cuarto carácter de `GPQ-0783), aunque tiene forma similar al de PZF. La comparación visual de ambos cuadros favorece 0 en las dos placas. Esta comprobación no reemplaza la revisión independiente.

## Estado del CSV puntual

El archivo `video_ground_truth_points_provisional.csv` contiene 18 puntos exactos. Se corrigieron las lecturas 660, 5197, 8408 y 14817; se agregó P003 en el cuadro 1312; se confirmó PZF en 4817 y 16506; y se retiró el punto 7842. Esas 18 etiquetas ya no son las mismas que las usadas para las métricas históricas publicadas, que deben recalcularse.


## Borrador de intervalos por pasada

Se publicó `video_ground_truth_intervals_provisional.csv` con 21 pasadas legibles transcritas de la hoja de anotación ciega. Incluye las lecturas visuales ya resueltas de P003 (`POD-0350`) y PZF (`PZF-0329`). Se excluyeron P015, donde no se ve la placa, y P018, cuyos caracteres siguen ambiguos.

Los límites se copiaron de la hoja de anotación. Aunque están expresados en números de cuadro, todavía no se han confirmado cuadro a cuadro. Tampoco se ha demostrado que la lista cubra todos los vehículos omitidos por el detector. Este borrador no sustituye `video_ground_truth.csv` ni permite publicar métricas integrales. Falta verificar límites y cobertura con una revisión humana independiente.

## Pendiente para evaluar el video completo

- Revisar los puntos en que las lecturas anteriores y la anotación coinciden, para detectar errores compartidos.
- Revisar el video completo, incluir todas las pasadas —también los vehículos omitidos por el detector— y anotar límites inclusivos del primer y último cuadro legible.
- Confirmar los límites cuadro a cuadro y pedir una revisión independiente de placas y límites sin mostrar predicciones; documentar discrepancias y casos ilegibles.
- Ejecutar 6.9 y 7.2 con la referencia de intervalos validada.

Hasta entonces, las métricas de la muestra puntual corregida no son una evaluación integral ni una tasa de error de todo el video. El video tiene 18.115 cuadros a 30 fps según sus metadatos; no se cotejó el hash con una copia externa. Las 21 imágenes de garita y su evaluación por imagen son un conjunto distinto.
