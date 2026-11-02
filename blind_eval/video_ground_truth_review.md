# Referencia final de `video_camiones.mp4`

## Archivo final

**[`video_ground_truth.csv`](video_ground_truth.csv) es la referencia final del video para la sección 7.2.** Los demás CSV de esta carpeta son plantillas o borradores históricos y no deben usarse para evaluar.

| Aspecto | Valor |
|---|---|
| Columnas | `plate_gt,frame_start,frame_end` |
| Filas | 20 pasadas legibles, una fila por pasada; 17 placas distintas |
| Placas | Formato del notebook, `XXX-0000`; las placas antiguas de 3 dígitos llevan un 0 inicial (`TAK-131` → `TAK-0131`) |
| Cuadros | Enteros desde 0, con límites inclusivos: primer y último cuadro en que la placa se transcribe con seguridad |
| Video | `video_camiones.mp4` del Release `datos-garita-v1`: 1280×720, 30 fps constantes, 18.115 cuadros (0 a 18.114), SHA-256 `87744d76bdccb9c90dbd2d1c2d27f8dc08e34a341b4ca1b1cac2ff6382f478ce` |

La sección 0 del notebook copia este archivo a `/content/SIRAP_workspace/video_ground_truth.csv`, y la 7.2 lo identifica como «referencia final publicada». El archivo cumple las validaciones de 7.1 y 7.2: placas con formato, cuadros dentro del rango y ningún intervalo solapado.

## Cómo se obtuvo

1. **Revisión 1 (R1).** Anotación ciega del video completo, hecha con Claude (asistente de IA de Anthropic). Usó solo el video original, sin predicciones, salidas OCR, etiquetas anteriores ni la hoja de cotejo.
2. **Revisión 2 (R2).** Segunda anotación ciega del video completo, hecha por el usuario en una revisión separada de R1. El usuario indicó que completó esa hoja sin consultar las lecturas anteriores. No vio R1, las lecturas OCR ni las discrepancias antes de terminar la anotación.
3. **Cotejo.** Se emparejaron las pasadas por solapamiento de cuadros y se compararon placas, pasadas y límites.
4. **Adjudicación en el video original.** Después, el usuario revisó las discrepancias con conocimiento de las lecturas anteriores, usando recortes ampliados, promedios de cuadros con el camión detenido y comparación con los mismos caracteres en otras placas del video. Esta adjudicación posterior no fue ciega. Si un carácter no se pudo resolver, la placa quedó fuera de la referencia; no se completó por intuición ni se tomó del OCR.
5. **Regla de límites.** Si la diferencia entre R1 y R2 era de umbral (la placa se acerca o se aleja y se vuelve legible de a poco), se usó el tramo en que ambas la consideran segura: el inicio más tardío y el fin más temprano. Si el video mostraba un hecho objetivo, como la placa entrando o saliendo del cuadro, se usó ese cuadro.

## Resultado del cotejo

- **Pasadas.** R1 y R2 encontraron las mismas 22 pasadas. R1 registró además un fragmento (cuadros 9296–9304) en el que solo se ve el costado de un vehículo que sale del cuadro; la placa nunca es visible y no entra a la referencia.
- **Placas.**
  - 19 de las 22 placas coincidieron entre R1 y R2, incluidas las dos lecturas parciales.
  - Se resolvieron 3 diferencias:
    - `PZF-0329`, en las dos pasadas: el carácter es un 0, con la forma de los 0 de otras placas del video.
    - `ABT-8220`: el carácter es una T. Con el carácter completo y 94 cuadros promediados, su barra superior es mucho más ancha que la base.
  - Quedaron 2 placas dudosas en ambas revisiones, que se excluyen.
- **Límites.** Los finales casi coinciden, con 3 cuadros de diferencia como máximo. Los inicios difieren más donde la placa entra pequeña. Las mayores diferencias fueron `GBP-9871` (3741 frente a 3812) y `GBQ-3986` (17004 frente a 16952), y se resolvieron con la regla de límites.

| Pasada | Placa en la referencia | Cuadros | Estado |
|---|---|---|---|
| P001 | — (lectura parcial `LBA-77?3`) | 0–247 | Excluida: el 3.er dígito puede ser 6 u 8; dudosa en R1 y R2 |
| P002 | `GRW-5172` | 472–827 | Coincidencia |
| P003 | — (lectura parcial `PO?-350`) | 1142–1488 | Excluida: el 3.er carácter es probablemente D, pero podría ser U o J; dudosa en R1 y R2 |
| P004 | `TAK-0131` | 1489–1916 | Coincidencia; placa antigua de 3 dígitos |
| P005 | `PAA-2178` | 1945–2301 | Coincidencia |
| P006 | `PAB-6510` | 2380–2771 | Coincidencia |
| P007 | `PTD-0533` | 3150–3696 | Coincidencia |
| P008 | `GBP-9871` | 3812–4076 | Coincidencia |
| P009 | `GTA-6721` | 4426–4774 | Coincidencia; imagen con bruma |
| P010 | `PZF-0329` | 4775–4899 | Resuelta: 4.º carácter 0 |
| P011 | `ABT-8220` | 5138–5714 | Resuelta: 3.er carácter T (R1 había leído I) |
| P012 | `GBO-5174` | 6142–6389 | Coincidencia; la placa sale por la izquierda desde 6390 |
| P013 | `GBN-2864` | 6593–7287 | Coincidencia; entra completa en 6593 y sale por abajo después de 7287. Humo entre ~6604 y ~6676 |
| P014 | `GBQ-2106` | 8373–9295 | Coincidencia; antes de 8373, el resplandor de los neblineros tapa la placa |
| — | — | 9296–9304 | Excluida: costado de un vehículo, sin placa visible (solo R1) |
| P016 | `GLB-0246` | 9814–10547 | Coincidencia; la lluvia interrumpe la lectura en tramos cortos |
| P017 | `GBQ-6255` | 11304–12214 | Coincidencia |
| P018 | `GBQ-2801` | 12784–13430 | Coincidencia; R1 la marcó como parcial por bajo contraste, pero R2 dio la misma cadena |
| P019 | `PAB-6510` | 13622–14410 | Coincidencia; el mismo vehículo de P006 vuelve a pasar |
| P020 | `GPQ-0783` | 14800–15338 | Coincidencia |
| P021 | `GBO-5174` | 15804–16473 | Coincidencia; el mismo vehículo de P012 vuelve a pasar |
| P022 | `PZF-0329` | 16474–16598 | Resuelta: es el clip de P010 repetido idéntico en el video |
| P023 | `GBQ-3986` | 17004–18080 | Coincidencia |

Los identificadores son los de R1.

## Limitaciones

- **Procedencia y revisión.** R1 se hizo con Claude (asistente de IA de Anthropic); R2 fue una anotación ciega hecha por el usuario en una revisión separada, según indicó, sin consultar las lecturas anteriores. La adjudicación posterior de discrepancias sí conocía esas lecturas y no fue ciega. No hubo una tercera revisión humana independiente; las métricas de 7.2 deben informar esta procedencia y sus límites.
- **Cobertura.** La referencia cubre 20 de las 22 pasadas con placa. Las lecturas del pipeline en los cuadros 0–247 y 1142–1488 quedan sin referencia y 7.2 no las puntúa.
- **Clip duplicado.** Las filas `PZF-0329` de 4775–4899 y 16474–16598 corresponden al mismo clip repetido en la edición del video. Se anotan dos veces porque el pipeline lo procesa dos veces.
- **Límites conservadores.** La regla del tramo común puede acortar algunos intervalos frente al rango en que una de las revisiones ya leía la placa.
- **Privacidad.** El CSV contiene placas reales. Se publica intencionalmente como artefacto del proyecto, igual que [`data/authorized_plates.csv`](../data/authorized_plates.csv).

## Archivos anteriores (históricos)

- [`video_ground_truth_points_provisional.csv`](video_ground_truth_points_provisional.csv): 18 cuadros puntuales armados antes de la referencia final. Contiene `ABI-8220`, que es un error (la placa es `ABT-8220`), y `LBA-7763` y `POD-0350`, que quedaron como dudosas en la referencia final. No usar en 7.2.
- [`video_ground_truth_intervals_provisional.csv`](video_ground_truth_intervals_provisional.csv): borrador de 21 intervalos copiado de R1 antes del cotejo. Lo reemplaza `video_ground_truth.csv`.
- Un cotejo anterior, no ciego, contra las lecturas previas al cotejo final:
  - Corrigió `GRW-5172`, `GBQ-2106`, `GLB-0246` y `GPQ-0783`, y retiró el punto 7842, en el que no hay vehículo visible. Esas correcciones se mantienen en la referencia final.
  - En cambio, sus conclusiones sobre `ABI-8220`, `POD-0350` y `LBA-7763` quedaron sustituidas por la adjudicación descrita arriba.

## Métricas

Las cifras publicadas de 7.2 (11/18 lecturas exactas y 9/16 placas recuperadas) se calcularon con una versión anterior de la referencia puntual, así que son históricas. Las métricas con la referencia final están pendientes: hay que ejecutar 6.9 y luego 7.2 en Colab con este archivo.
