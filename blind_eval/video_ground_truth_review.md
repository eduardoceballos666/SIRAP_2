# Revisión y cotejo provisional de `video_camiones.mp4`

## Alcance de la referencia puntual

La referencia pública contiene cuadros seleccionados, con `frame_start == frame_end`. Sirve para medir lecturas en esos puntos; no describe los intervalos completos de legibilidad ni incluye necesariamente todas las pasadas del video. No debe presentarse como evaluación integral.

La anotación ciega original se conserva aparte como registro histórico. El cotejo que se documenta abajo se hizo después de conocer las lecturas anteriores; por ello, no es una segunda revisión ciega ni una revisión independiente.

## Cotejo visual informado por la persona anotadora

La persona anotadora comunicó que volvió al video y cotejó 11 discrepancias. Comparó formas de caracteres con otras placas del mismo video. Los resultados y límites de lo que se pudo leer son:

| Caso | Lectura o hallazgo comunicado | Disposición para la referencia |
|---|---|---|
| P001, cuadro 208 | `LBA-7763`; la forma del dígito favorece 6 frente a 8. Confianza media-alta. | Se conserva `LBA-7763` como punto exacto. |
| P002, cuadro 660 | `GRW-5172`; el segundo carácter es R y el tercero W. | Se corrige de `GBR-5172` a `GRW-5172`. |
| P003, cerca del cuadro 1312 | `PDL-3501` no está respaldada; se ve `PO?-350`, con D más probable que U. No se distingue un cuarto dígito. | Excluido del CSV exacto hasta resolver la placa. |
| P011, cuadro 5197 | `ABI-8220`; el tercer carácter no coincide con T. | Se corrige de `ABT-8220` a `ABI-8220`. |
| P012, cuadro 6388 | `GBO-5174` es legible en ese cuadro y deja de verse desde 6392. | Hallazgo de intervalo pendiente; no se agregó al CSV de puntos porque ese cuadro no estaba en la selección publicada. |
| Cuadro 7842 | No aparece un vehículo; se ve el resplandor de los neblineros. `GBN-2864` sale del video en el corte de 7322. | Se elimina el punto 7842 por falta de sustento visual. |
| P014, cuadro 8408 | `GBQ-2106`; el tercer carácter tiene curva y cola, no la forma de D. | Se corrige de `GBD-2106` a `GBQ-2106`. |
| P016 | `GLB-0246`; el tercer carácter tiene dos lóbulos. | Se conserva `GLB-0246`; la referencia de intervalos anterior con `GLD-0246` queda marcada como errónea. |
| P017 | `GBQ-6255`; el tercer carácter es cerrado y tiene cola, no es V. | Hallazgo que debe incorporarse al cotejo de pasadas; no se añadió un cuadro puntual sin un índice confirmado. |
| P020, cuadro 14817 | `GPQ-0783`; la Q tiene cola. | Se corrige de `GPR-0783` a `GPQ-0783`. |
| P010/P022 | La placa empieza `PZF`; el carácter después del guion parece D, pero su forma coincide con el 0 de `GPQ-0783`. La anotadora señala que solo se leería como 0 si el equipo confirma el formato de cuatro dígitos. | No se elige una etiqueta por intuición. Se retiran del CSV exacto los puntos `PZF-0329` de los cuadros 4817 y 16506 mientras la lectura siga sin resolver. |

La anotadora también identificó una inconsistencia propia: no había marcado como dudoso el cuarto carácter de `GPQ-0783`, aunque tiene forma similar al de PZF. Se debe revisar ese patrón en las demás placas coincidentes antes de cerrar la referencia.

## Estado del CSV puntual

El archivo `video_ground_truth_points_provisional.csv` conserva ahora 15 puntos exactos. Se corrigieron los casos 660, 5197, 8408 y 14817; se retiró 7842 y se excluyeron los dos puntos PZF no resueltos. P003 sigue fuera de la referencia exacta. Estas métricas deben recalcularse y etiquetarse como resultados de una muestra puntual corregida, no como evaluación completa.

## Trabajo pendiente para evaluar el video completo

- Resolver P003 y PZF con evidencia suficiente; mantenerlos como dudosos si no se pueden leer.
- Revisar los puntos en que las lecturas anteriores y la anotación coinciden, para detectar errores compartidos.
- Revisar el video completo, incluir todas las pasadas —también las no detectadas— y anotar límites inclusivos de primer y último cuadro legible.
- Confirmar la frecuencia de cuadros del archivo original antes de convertir intervalos anotados en segundos a índices de cuadro.
- Pedir una revisión independiente de etiquetas y límites sin mostrar predicciones; documentar discrepancias y casos ilegibles.
- Ejecutar 6.9 y 7.2 con la referencia de intervalos validada. Hasta entonces, la tasa integral de error y las métricas de todos los vehículos siguen pendientes.

El video disponible en el repositorio tiene 18.115 cuadros según la anotación técnica previa; el hash del archivo original no se cotejó. Las 21 imágenes completas de garita y su evaluación por imagen son un conjunto distinto y no sustituyen la referencia temporal del video.
