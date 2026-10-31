# Revisión visual provisional de `video_camiones.mp4`

Fecha: 2026-10-30

Se revisaron visualmente los cuadros guía de los 44 eventos candidatos de la sección 7.1, tomando los caracteres de la placa física visible y sin usar el texto OCR/detector superpuesto como etiqueta. Las detecciones en la báscula vacía se descartaron; los eventos repetidos del mismo camión se consolidaron cuando eran claramente la misma pasada. Se transcribieron 18 observaciones con lectura visual suficientemente clara.

## Alcance de `video_ground_truth.csv`

Cada fila identifica un cuadro guía en el que la placa se pudo leer visualmente (`frame_start == frame_end`). Por eso el archivo sirve como referencia de cuadros puntuales, no como anotación completa de los intervalos de legibilidad ni de todos los vehículos del video. Las placas o cuadros ambiguos se omitieron, en lugar de inferir caracteres. Los puntos no se deben presentar como verdad de referencia completa para recall de todo el video.

## Pendiente antes de cerrar la evaluación completa

- Revisar el video original cuadro a cuadro para determinar el primer y último cuadro legible de cada pasada y buscar vehículos no incluidos en los 44 eventos del detector.
- Solicitar una segunda revisión humana independiente de las 18 transcripciones y de los límites de cada intervalo.
- Cargar la anotación completa en `MyDrive/proyecto_integrador_placas/video_ground_truth.csv` y luego ejecutar la sección 7.2. Las métricas del conjunto puntual serían métricas condicionadas a estos cuadros, no una evaluación completa del video ni del recall de vehículos.

Placas dudosas que no se incorporaron incluyen la del camión amarillo del cuadro 1312 y lecturas nocturnas con reflejo/oclusiones. También se descartaron recuadros OCR que apuntaban a texto lateral del camión en vez de a una placa.
