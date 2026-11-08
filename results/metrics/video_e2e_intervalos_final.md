# Evaluación del video de garita: secciones 6.9 y 7.2

La referencia publicada es [`blind_eval/video_ground_truth.csv`](../../blind_eval/video_ground_truth.csv): contiene 20 pasadas anotadas, 17 placas únicas e intervalos inclusivos. Dos pasadas dudosas (cuadros 0–247 y 1142–1488) siguen excluidas; por eso la referencia no cubre todas las pasadas identificadas en el video.

## Reejecución más reciente en Colab

En esta reejecución, la sección 6.9 procesó los 18.115 cuadros y registró 51 lecturas. La sección 7.2 pudo comparar 30 lecturas con la referencia:

| Indicador | Resultado |
|---|---:|
| Cuadros procesados por 6.9 | 18.115 |
| Lecturas registradas por 6.9 | 51 |
| Lecturas con referencia en 7.2 | 30/51 |
| Coincidencia exacta por lectura (EMR) | 18/30 (60 %) |
| Placas únicas de referencia recuperadas | 16/17 (94,12 %) |
| Falsas autorizaciones observadas entre lecturas clasificables | 2/30 (6,67 %) |
| Lecturas sin referencia | 21/51 (no clasificables) |

Estas cifras describen esta reejecución y no una cobertura integral del video. Las 21 lecturas sin referencia no se clasifican como aciertos o errores. La tasa integral de falsas autorizaciones para todo el video **no es estimable**. Las dos pasadas dudosas tampoco se incorporaron ni se completaron por inferencia.

## Corrida guardada anterior

La corrida guardada anteriormente procesó los mismos 18.115 cuadros y registró 34 lecturas. De ellas, 24 coincidieron con intervalos de referencia; obtuvo EMR de 17/24 (70,83 %), recall de placas únicas de 15/17 (88,24 %) y 0 falsas autorizaciones entre las 24 lecturas clasificables. Diez lecturas quedaron sin referencia. Esos valores pertenecen a una ejecución distinta y no deben combinarse con la reejecución más reciente.

## Alcance y reproducción

La referencia cubre 20 de las 22 pasadas con placa identificadas. La reejecución más reciente obtuvo EMR de 60 %, por debajo de la meta del proyecto de 80 %. Los resultados no deben extrapolarse a las dos pasadas excluidas ni presentarse como cobertura exhaustiva de todos los vehículos. El resultado histórico de 11/18 puntos y 9/16 placas corresponde a una referencia anterior y se conserva únicamente como antecedente en [`video_e2e_puntos_provisionales_20261101.md`](video_e2e_puntos_provisionales_20261101.md).

Para reproducir la evaluación, ejecuta la sección 0, las celdas previas requeridas para el pipeline completo, 6.9 y después 7.2 con el mismo video y el CSV de referencia.

## Interpretación estadística e intervalo de Wilson

El resultado 18/30 (60 %) es descriptivo de lecturas clasificables y no estima el video completo: 21 de 51 lecturas no tienen referencia y dos pasadas dudosas están excluidas. No se calcula un IC de Wilson para esta corrida porque la referencia es incompleta y las lecturas repetidas dentro de una pasada no son ensayos independientes. No se imputan ni ponderan las lecturas faltantes; hacerlo con la información publicada introduciría supuestos no verificables.

Como contraste, el holdout ciego aleatorio de imágenes SAVH tiene 42/57 exactas para OCR base (IC Wilson 95 %: 61,0–83,4 %) y 35/57 para el OCR afinado (48,4–72,9 %). Esa inferencia se limita a imágenes con referencia humana aprobada, independientes de la partición de desarrollo; no se debe trasladar a todas las condiciones de garita. Una imagen de las 58 seleccionadas quedó fuera por falta de referencia aprobada.

Para una estimación representativa de operación, el marco debe cubrir las pasadas objetivo, muestrear pasadas aleatoriamente por cámara y condición de captura, etiquetar todas las unidades muestreadas a ciegas y resolver referencias faltantes antes de puntuar. El protocolo completo está en docs/evaluacion_representativa.md y el cálculo reproducible en notebooks/Evaluacion_IC_Wilson_y_muestreo.ipynb.
