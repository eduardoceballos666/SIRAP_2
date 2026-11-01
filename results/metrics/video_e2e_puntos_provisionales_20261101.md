# Resultado provisional de puntos de referencia del video

Fecha del registro: 2026-11-01.

Este archivo registra únicamente la salida agregada de la ejecución 7.2 del notebook en Colab frente a las 18 observaciones puntuales privadas existentes. No es una evaluación completa del video ni una validación humana independiente.

| Medida | Resultado |
|---|---:|
| Lecturas emitidas por el pipeline | 52 |
| Lecturas comparables en los cuadros de referencia | 18 |
| Coincidencia exacta en cuadros de referencia | 10/18 (55.6%) |
| Etiquetas de placa únicas de referencia detectadas en esos puntos | 8/16 (50.0%) |

Alcance y limitaciones:

- Las 18 referencias son cuadros puntuales (frame_start == frame_end), no intervalos completos ni un censo de pasadas. No permiten estimar recall del video completo.
- Las 34 lecturas restantes no coinciden con una fila de referencia en ese mismo cuadro. No se clasifican como falsos positivos porque la referencia es dispersa.
- El 50.0% es recall sobre 16 etiquetas de placa únicas en los puntos revisados; no equivale a recall por pasada/vehículo y puede verse afectado por pasadas repetidas.
- La referencia actual fue preparada como anotación provisional por un evaluador. La segunda revisión humana independiente y la adjudicación siguen pendientes.
- No se publica ninguna placa, clave de respuestas ni predicción individual.

Para cerrar la evaluación punta a punta, se necesita una referencia completa de intervalos por pasada, inclusión de vehículos omitidos por el detector, revisión ciega independiente y ejecución de la sección 7.2 contra el mismo video de 18,115 cuadros procesado por el pipeline. Mantén results/metrics/e2e.json sin EMR/CER completos hasta completar esos pasos.
