# Avisos de componentes y recursos de terceros

La licencia MIT de [LICENSE](LICENSE) cubre el código original de SIRAP. No sustituye las licencias ni las condiciones aplicables a modelos, pesos, bibliotecas o conjuntos de datos de terceros.

## Modelos y bibliotecas

- **Ultralytics YOLO11:** detector utilizado para localizar placas. Los pesos entrenados con Ultralytics están sujetos a AGPL-3.0, conforme a las condiciones de Ultralytics.
- **fast-plate-ocr:** biblioteca de reconocimiento óptico de caracteres (OCR) distribuida bajo MIT.
- **OpenCV (`opencv-python-headless` 4.12.0.88):** operaciones auxiliares de redimensionado y codificación JPEG. No realiza la detección de placas; esta corresponde a YOLO11. Licencia Apache 2.0 ([texto oficial](https://github.com/opencv/opencv/blob/4.12.0/LICENSE)).

## Conjuntos de datos

- **License Plate Recognition — Roboflow Universe:** conjunto de datos utilizado para entrenar y evaluar el detector, bajo CC BY 4.0. Consulte la [ficha del conjunto](https://universe.roboflow.com/roboflow-universe-projects/license-plate-recognition-rxg4e) para sus condiciones de atribución.
- **SAVH Guayaquil ANPR Plate Images Dataset — Zenodo:** utilizado para evaluar OCR con placas ecuatorianas. El registro consultado no muestra una licencia para el archivo específico; revise sus condiciones antes de redistribuirlo.

Las marcas, derechos y licencias de cada componente y recurso pertenecen a sus titulares. Para el inventario de otras dependencias de software, consulte la sección de [agradecimientos y referencias](README.md#11-agradecimientos-y-referencias).
