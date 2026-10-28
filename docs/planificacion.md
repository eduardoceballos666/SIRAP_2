# Planificación del proyecto – SIRAP 1.0 (FastAPI + Vue 3)

**Proyecto Integrador en IA (MIAR0545)** · Eduardo Alejandro Ceballos Jijón · Christian Xavier Valle Maridueña
Periodo: 12/09/2026 – 24/10/2026 (6 semanas) · Dedicación: ≈8 h/semana por integrante (Python / Google Colab)

> **Versionado:** la versión del producto es **SIRAP 1.0**. La API y el paquete frontend registran **2.0.0** como versiones de sus componentes. El tag `v2.0` identifica el corte técnico del repositorio asociado a la arquitectura FastAPI + Vue 3, no una versión 2.0 del producto.

---

## 1. Definición del problema

En urbanizaciones, edificios, empresas y plantas industriales el control vehicular en la garita se hace a mano: el
guardia mira la placa, la busca en una lista impresa o en una hoja de cálculo, la anota en un cuaderno y abre la
barrera. Esto genera **colas** en horas pico, **errores de transcripción**, **listas desactualizadas** y un historial
difícil de auditar. El caso de partida del proyecto fue el ingreso de camiones a una planta, donde cada placa se
verifica en la garita antes de levantar la barrera.

**SIRAP** automatiza ese flujo: una cámara captura el vehículo, un detector localiza la placa, un OCR la lee, el
sistema la busca en los archivos CSV y propone una decisión (*autorizado*, *denegado*, *no registrado* o
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
| O6 | Entregar una interfaz usable | App web FastAPI + Vue 3 con los 4 módulos de la guía de diseño, inicio de sesión y Acerca del modelo | Desplegada en Hugging Face Spaces |

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
- Tablas operativas CSV de vehículos y propietarios, listas/autorizaciones, garitas, usuarios e historial.
- **Aplicación web SIRAP 1.0:** API REST en FastAPI con autenticación por usuario y roles (operador, supervisor,
  administrador) y frontend en Vue 3 (Vite, Pinia, Vue Router, Tailwind CSS) con Dashboard, Reconocimiento y Acceso,
  Historial (con exportación CSV), Administración y Acerca del modelo; publicada en Hugging Face Spaces con Docker.
- Pipeline de video y modo en vivo en el notebook (seguimiento OC-SORT, voto de lecturas).
- Consultas públicas programadas al SRI para completar marca/modelo/año y a EcuadorLegalOnline para buscar el nombre visible asociado a la placa. La interfaz no muestra ese nombre y ninguna consulta interviene en la decisión de acceso; la exportación enriquecida separada puede guardarlo si está configurada.
- Documentación técnica, ética y manual de usuario; pruebas unitarias.

**No incluye (trabajo futuro)**

- Control físico real de la barrera: la versión entregada usa una **barrera simulada** (existe la integración
  HTTP con token, pero no se conectó a un relé/PLC).
- Conexión directa de la app web a las cámaras IP de la garita (la app recibe imágenes o la cámara del navegador;
  el video en vivo corre en el notebook).
- Gestión avanzada de cuentas (recuperar contraseña, bloqueo por intentos fallidos, inicio de sesión único de la
  empresa).
- Reconocimiento de placas de motos o de otros países.

## 5. Cronograma (planificado vs real)

| Semana | Planificado | Real |
|---|---|---|
| 1 (12–18/09) | Problema, objetivos, búsqueda de datasets | Problema definido; datasets CCPD y SAVH Guayaquil identificados |
| 2 (19–25/09) | Ficha de decisión técnica y arquitectura | Ficha v1 (21/09): YOLOv8 + EasyOCR/PaddleOCR; el 25/09 se cambió el detector a RF-DETR + OC-SORT |
| 3 (26/09–02/10) | Preparación de datos y primer entrenamiento | Dataset de Roboflow (10 125 imágenes) como base de detección; SAVH para el OCR |
| 4 (03–09/10) | Pipeline completo y regla de decisión | 07/10: YOLOv8n, normalización, validación de formato y regla de 3 estados |
| 5 (10–16/10) | Optimización y evaluación | Lista de autorizaciones CSV, verificación SRI, registros CSV, pipeline de video y modo en vivo |
| 6 (17–24/10) | Interfaz, documentación y videos | 23/10: detector final YOLO11-s y OCR fast-plate-ocr; versión inicial de SIRAP; repositorio y documentación. 24/10: afinamiento del OCR, estudio de hiperparámetros (Optuna, 24 *trials*) y **SIRAP 1.0 (arquitectura FastAPI + Vue 3)** publicada en Hugging Face Spaces |

**Desviaciones.** El detector cambió cuatro veces (YOLOv8 → RF-DETR → YOLOv8n → YOLO11-s) y el OCR también
cambió hasta llegar a fast-plate-ocr. Los cambios se debieron al costo de cómputo en Colab (RF-DETR es pesado) y a la
necesidad de correr en CPU dentro de la app. Esto desplazó la optimización de
hiperparámetros al último día (ver `optimizacion.md`). La versión web FastAPI + Vue no estaba en el plan original:
se agregó al final para tener una arquitectura cliente-servidor con autenticación por usuario.

## 6. Recursos

| Tipo | Recurso |
|---|---|
| Datos | License Plate Recognition v11 (Roboflow, CC BY 4.0); SAVH Guayaquil (Zenodo); imágenes y video de la garita (con autorización); lista de placas autorizadas en CSV |
| Hardware | Google Colab con GPU (T4 para pruebas; el entrenamiento final y las mediciones se hicieron en una NVIDIA L4); CPU para el OCR y la app; Hugging Face Spaces (Docker) para SIRAP 1.0 |
| Software | Python 3.11+, Ultralytics 8.4.177, fast-plate-ocr 1.1.0, ONNX Runtime, supervision, trackers (OC-SORT), CSV, FastAPI, Vue 3, Vite, Pinia, Vue Router, Tailwind CSS, ECharts, Docker |
| Personas | 2 integrantes, ≈8 h/semana cada uno |

## 7. Riesgos y mitigación

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| Dataset no representa placas ecuatorianas | Alta | Alto | OCR validado con SAVH Guayaquil; *test* con imágenes reales de la garita; normalización al formato local |
| Sesión de Colab se cae durante el entrenamiento | Alta | Medio | Todo en Drive; el entrenamiento se reanuda desde la última época |
| Lectura incorrecta que abre la barrera | Media | Alto | Umbral de confianza, verificación manual, confirmación del operador, lista restringida con prioridad |
| Modelos pesados para la nube | Media | Medio | YOLO11-s exportado a ONNX + OCR de 5 MB en CPU |
| Llaves de API expuestas | Media | Alto | Secretos de entrenamiento y despliegue; se revocaron las llaves que quedaron en una versión antigua del notebook |
| Datos personales (placas, propietarios) | Alta | Alto | Datos ficticios en la demo; minimización; ver `consideraciones_eticas.md` |
| Cambios de tecnología a mitad del proyecto | Alta | Medio | Pipeline modular: detector, OCR y decisión se cambian por separado |
| La plataforma de despliegue no da recursos gratuitos | Media | Medio | Ocurrió: fue necesario pagar a Hugging Face para que el Space Docker pudiera ejecutar la aplicación; sin el pago no corría. La imagen Docker sigue siendo portátil y se analizaron alternativas (Render y Railway: 512 MB, insuficientes para ≈410 MB de la API) |
| Acceso no autorizado a la app publicada | Media | Alto | Inicio de sesión con contraseña (PBKDF2), JWT con vencimiento, permisos por rol y decisión recalculada en el servidor |

## Umbral operativo OCR

La aplicación usa un umbral de confianza OCR de **99 %**. Las lecturas por debajo pasan a verificación manual.
