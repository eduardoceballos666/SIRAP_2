# Evaluación final del video de garita: secciones 6.9 y 7.2

La corrida guardada procesó el video completo con 18.115 cuadros en la sección 6.9 y usó como referencia la versión final [`blind_eval/video_ground_truth.csv`](../../blind_eval/video_ground_truth.csv), con 20 pasadas anotadas y límites inclusivos.

## Resultados de 7.2

| Indicador | Resultado |
|---|---:|
| Lecturas del pipeline (6.9) | 34 |
| Lecturas dentro de intervalos de referencia | 24/34 |
| Coincidencia exacta por lectura (EMR) | 17/24 (70,83 %) |
| Placas únicas de referencia recuperadas | 15/17 (88,24 %) |
| Falsas autorizaciones entre lecturas clasificables | 0/24 |
| Lecturas sin referencia | 10/34 (no clasificables) |
| Pasadas de referencia fuera del tramo procesado | 0 |

La tasa integral de falsas autorizaciones **no es estimable**: las 10 lecturas que caen fuera de los intervalos no tienen una etiqueta real asociada, por lo que no se clasifican como aciertos ni errores. El resultado 0/24 corresponde solo a las lecturas que sí pudieron compararse con la referencia; no equivale a cero falsas autorizaciones en todo el video.

## Alcance y procedencia

La referencia contiene 20 pasadas y 17 placas únicas; cubre 20 de las 22 pasadas con placa identificadas. Se excluyeron dos pasadas dudosas (cuadros 0–247 y 1142–1488).

El EMR de 70,83 % queda por debajo de la meta del proyecto de 80 %. Los resultados describen la corrida y la referencia publicadas; no deben extrapolarse a las dos pasadas excluidas ni presentarse como cobertura exhaustiva de todos los vehículos. El resultado histórico de 11/18 puntos y 9/16 placas corresponde a una referencia anterior y se conserva únicamente como antecedente en [`video_e2e_puntos_provisionales_20261101.md`](video_e2e_puntos_provisionales_20261101.md).

Para reproducir la evaluación, ejecuta la sección 0, las celdas previas requeridas para el pipeline completo, 6.9 y después 7.2 con el mismo video y el CSV final.
