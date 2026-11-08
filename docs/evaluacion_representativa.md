# Evaluación representativa e intervalos de Wilson

## Alcance actual

Los resultados de OCR con mayor sustento estadístico son los del holdout ciego SAVH: se seleccionaron aleatoriamente 58 imágenes fuera de la partición de desarrollo y 57 tuvieron una referencia aprobada. La única imagen excluida no tenía fila en la referencia aprobada. En las 57 imágenes puntuables, el OCR base acertó 42 y el afinado 35.

El IC de Wilson del 95 % para el OCR base es 61,0–83,4 % (42/57); para el afinado, 48,4–72,9 % (35/57). Estos intervalos describen la incertidumbre de la proporción en esa muestra. La inferencia queda condicionada a imágenes SAVH con referencia aprobada; no demuestra representatividad de todas las garitas, horarios, distancias, cámaras, provincias o condiciones de operación. La exclusión de una imagen debe conservarse visible y resolverse mediante una referencia adjudicada o una sustitución aleatoria predefinida.

El resultado del video de garita sigue siendo parcial: 30 de 51 lecturas pudieron compararse, 21 quedaron sin referencia y dos pasadas dudosas se excluyeron. El 18/30 es una tasa descriptiva solo de lecturas clasificables. No es una estimación del video completo. Las lecturas pueden repetirse dentro de la misma pasada y no son ensayos independientes; por eso no se calcula un Wilson ingenuo sobre 30 lecturas. Tampoco se imputan las 21 faltantes como aciertos o errores.

## Qué se calcula

Para una proporción binomial, con x éxitos de n ensayos independientes, p̂ = x/n. El intervalo score de Wilson usa el cuantil normal z y queda dentro de [0, 1], a diferencia del intervalo normal simple. Para 95 %, z ≈ 1,96. La función wilson_interval de src/evaluate.py devuelve conteos, estimación, nivel, límites y método. En la evaluación punta a punta, el IC solo se devuelve cuando el CSV incluye unit_id no nulos y únicos: un ID por imagen independiente o pasada, nunca por cuadro repetido. Si falta esa columna, se conserva la métrica descriptiva, pero el CI queda sin reportar.

Aplicaciones apropiadas: lectura exacta por imagen o pasada independiente, formato válido por unidad, cobertura de lectura por unidad y recuperación de placas únicas. Para detector, precisión/recall requieren TP, FP y FN al umbral definido; no se debe derivar un Wilson de mAP, F1 o promedios de clases sin sus conteos subyacentes. CER, latencia media y mAP tampoco son proporciones binomiales.

## Protocolo para una evaluación representativa

1. **Definir la población y el periodo.** Por ejemplo: todas las pasadas de vehículos por las garitas seleccionadas durante las semanas de evaluación. Registrar qué cámaras y periodos cubre la conclusión.
2. **Muestrear la unidad independiente.** Para video, la unidad es la pasada de un vehículo, no cada cuadro, cada OCR ni cada lectura repetida. Para datos de imágenes, evitar que varias fotos del mismo vehículo aparezcan como ensayos independientes.
3. **Construir estratos antes de ver predicciones.** Incluir garita/cámara, día/noche, distancia o tamaño de placa, ángulo/oclusiones y tipo de vehículo cuando formen parte del uso previsto. Seleccionar aleatoriamente dentro de cada estrato. Usar asignación proporcional si se quiere un Wilson agregado sin ponderación; si se sobremuestrean estratos difíciles, informar resultados por estrato y una estimación ponderada con intervalo apropiado, no un Wilson simple sobre el total.
4. **Anotar sin ver las predicciones.** Dos revisores humanos transcriben y delimitan cada pasada de forma independiente. Un tercero resuelve desacuerdos. La legibilidad se determina con reglas predefinidas; una predicción fallida sobre una placa legible cuenta como error, no se elimina del denominador.
5. **Tratar las etiquetas faltantes sin sesgo de selección.** No excluir casos porque el sistema no los detectó o porque la placa resulte difícil. Completar/adjudicar la etiqueta o informar por separado la fracción no evaluable y límites de sensibilidad. Toda sustitución se sortea del mismo marco muestral y se registra.
6. **Congelar y evaluar.** Guardar semilla, marco muestral, probabilidades de inclusión, exclusiones, anotaciones adjudicadas, versión del modelo y umbrales antes de ejecutar el modelo. No ajustar el modelo con este holdout.
7. **Informar alcance y conteos.** Publicar x/n, porcentaje, IC, nivel de confianza, población objetivo, estratos, exclusiones, datos faltantes y limitaciones. Un IC estrecho no corrige cobertura incompleta ni selección sesgada.

La corrección metodológica no convierte retroactivamente la referencia parcial del video en representativa. Para conseguir esa inferencia hay que terminar el marco de pasadas y las etiquetas humanas que faltan, o seleccionar una nueva muestra aleatoria completa siguiendo el protocolo. Si se anota exhaustivamente un video finito, reportar su resultado como censo de ese video; el intervalo solo corresponde a la generalización a otros periodos/vehículos.

## Cálculo reproducible del holdout

Ejecuta notebooks/Evaluacion_IC_Wilson_y_muestreo.ipynb. El notebook reproduce los intervalos a partir de los conteos publicados y marca como no estimable cualquier proporción cuyo denominador no tenga etiquetas completas o unidades independientes.
