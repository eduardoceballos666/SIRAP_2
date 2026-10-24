# Planificación del proyecto – SIRAP

**Proyecto Integrador en IA (MIAR0545)** · Eduardo Alejandro Ceballos Jijón · Christian Xavier Valle Maridueña
Periodo: 12/09/2026 – 24/10/2026 (6 semanas) · Dedicación: ≈8 h/semana por integrante (Python / Google Colab)

---

## 1. Definición del problema

En urbanizaciones, edificios, empresas y plantas industriales el control vehicular en la garita se hace a mano: el
guardia mira la placa, la busca en una lista impresa o en una hoja de cálculo, la anota en un cuaderno y abre la
barrera. Esto genera **colas** en horas pico, **errores de transcripción**, **listas desactualizadas** y un historial
difícil de auditar. El caso de partida del proyecto fue el ingreso de camiones a una planta, donde cada placa se
verifica en la garita antes de levantar la barrera.

**SIRAP** automatiza ese flujo: una cámara captura el vehículo, un detector localiza la placa, un OCR la lee, el
sistema la busca en la base de datos y propone una decisión (*autorizado*, *denegado*, *no registrado* o
*verificación manual*). El operador confirma y la operación queda registrada.

## 2. Objetivos

**General.** Construir un sistema de reconocimiento automático de placas (ALPR) y control de acceso, usable por
un operador de garita, que lea placas ecuatorianas y registre cada operación.

**Específicos y metas medibles**

| # | Objetivo | Métrica | Meta |
|---|---|---|---|
| O1 | Detectar la placa en la imagen | mAP@0.5 en *test* | ≥ 0,85 |
| O2 | Leer la placa completa sin errores | Exact Match Rate (EMR) | ≥ 80 % |
| O3 | Responder a tiempo para la garita | Tiempo punta a punta por imagen | ≤ 1 s |
| O4 | No decidir a ciegas | Lecturas dudosas enviadas a verificación manual | 100 % bajo el umbral |
| O5 | Auditar | Operaciones registradas con fecha, garita, operador, placa y resultado | 100 % |
| O6 | Entregar una interfaz usable | App Streamlit con los 4 módulos de la guía de diseño | Desplegada |

## 3. Justificación y relevancia

- **Operativa:** menos tiempo por vehículo y menos errores de digitación.
- **Seguridad:** listas blancas y restringidas consultadas en el momento, no de memoria.
- **Trazabilidad:** historial completo para auditoría (quién abrió, cuándo, por qué).
- **Local:** las placas ecuatorianas tienen un formato propio (`ABC-1234`, y `ABC-123` en placas antiguas) y la
  mayoría de sistemas comerciales no están ajustados a él. El proyecto valida el OCR con placas reales de Guayaquil.

## 4. Alcance

**Incluye**

- Detector de placas YOLO11-s entrenado y evaluado; OCR `fast-plate-ocr`; normalización al formato ecuatoriano.
- Regla de decisión con listas blanca/restringida, umbral de confianza y detección de lecturas «casi iguales».
- Base de datos (PostgreSQL en producción, SQLite en la demo) con vehículos, propietarios, listas, garitas,
  usuarios e historial.
- Aplicación Streamlit: Dashboard, Reconocimiento y Acceso, Historial (con exportación CSV), Administración y
  Acerca del modelo.
- Pipeline de video y modo en vivo en el notebook (seguimiento OC-SORT, voto de lecturas).
- Documentación técnica, ética y manual de usuario; pruebas unitarias.

**No incluye (trabajo futuro)**

- Control físico real de la barrera: la versión entregada usa una **barrera simulada** (existe la integración
  HTTP con token, pero no se conectó a un relé/PLC).
- Conexión directa de la app web a las cámaras IP de la garita (la app recibe imágenes o la cámara del navegador;
  el video en vivo corre en el notebook).
- Integración con SRI / ANT en la app (se probó en el notebook; depende de acceso a esos servicios).
- Autenticación completa con contraseñas por usuario (la demo usa un PIN de administración opcional).
- Reconocimiento de placas de motos o de otros países.

## 5. Cronograma (planificado vs real)

> Las fechas de la columna «Real» salen del registro de decisiones del equipo; las semanas 3 y 5 resumen el trabajo
> de esos días y deben ajustarse con la bitácora del equipo si difieren.

| Semana | Planificado | Real |
|---|---|---|
| 1 (12–18/09) | Problema, objetivos, búsqueda de datasets | Problema definido; datasets CCPD y SAVH Guayaquil identificados |
| 2 (19–25/09) | Ficha de decisión técnica y arquitectura | Ficha v1 (21/09): YOLOv8 + EasyOCR/PaddleOCR; el 25/09 se cambió a RF-DETR + OC-SORT + GLM-OCR |
| 3 (26/09–02/10) | Preparación de datos y primer entrenamiento | Dataset de Roboflow (10 125 imágenes) como base de detección; SAVH para el OCR |
| 4 (03–09/10) | Pipeline completo y regla de decisión | 07/10: YOLOv8n + GLM-OCR local, normalización, validación de formato y regla de 3 estados |
| 5 (10–16/10) | Optimización y evaluación | Base de la planta en PostgreSQL, verificación SRI, pipeline de video y modo en vivo |
| 6 (17–24/10) | Interfaz, documentación y videos | 23/10: detector final YOLO11-s y OCR fast-plate-ocr; app SIRAP en Streamlit; repositorio y documentación |

**Desviaciones.** El detector cambió cuatro veces (YOLOv8 → RF-DETR → YOLOv8n → YOLO11-s) y el OCR tres
(EasyOCR/PaddleOCR → GLM-OCR → fast-plate-ocr). Los cambios se debieron a costo de cómputo en Colab (RF-DETR y
GLM-OCR son pesados) y a la necesidad de correr en CPU dentro de la app. Esto consumió tiempo que estaba previsto
para la optimización de hiperparámetros (ver `optimizacion.md`).

## 6. Recursos

| Tipo | Recurso |
|---|---|
| Datos | License Plate Recognition v11 (Roboflow, CC BY 4.0); SAVH Guayaquil (Zenodo); imágenes y video de la garita (con autorización); base de la planta |
| Hardware | Google Colab con GPU (T4 para pruebas; el entrenamiento final y las mediciones se hicieron en una NVIDIA L4); CPU para el OCR y la app; Streamlit Community Cloud (despliegue) |
| Software | Python 3.11+, Ultralytics 8.4.177, fast-plate-ocr 1.1.0, ONNX Runtime, supervision, trackers (OC-SORT), PostgreSQL / psycopg 3, Streamlit, Plotly |
| Personas | 2 integrantes, ≈8 h/semana cada uno |

## 7. Riesgos y mitigación

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| Dataset no representa placas ecuatorianas | Alta | Alto | OCR validado con SAVH Guayaquil; *test* con imágenes reales de la garita; normalización al formato local |
| Sesión de Colab se cae durante el entrenamiento | Alta | Medio | Todo en Drive; el entrenamiento se reanuda desde la última época |
| Lectura incorrecta que abre la barrera | Media | Alto | Umbral de confianza, verificación manual, confirmación del operador, lista restringida con prioridad |
| Modelos pesados para la nube | Media | Medio | YOLO11-s exportado a ONNX + OCR de 5 MB en CPU |
| Llaves de API expuestas | Media | Alto | Secretos de Colab/Streamlit; se revocaron las llaves que quedaron en una versión antigua del notebook |
| Datos personales (placas, propietarios) | Alta | Alto | Datos ficticios en la demo; minimización; ver `consideraciones_eticas.md` |
| Cambios de tecnología a mitad del proyecto | Alta | Medio | Pipeline modular: detector, OCR y decisión se cambian por separado |
