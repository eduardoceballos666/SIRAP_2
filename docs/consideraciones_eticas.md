# Consideraciones éticas – SIRAP 1.0

> **Versionado:** SIRAP es el producto versión **1.0**. API 2.0.0, paquete frontend 2.0.0 y tag GitHub `v2.0` son identificadores técnicos de componentes/código; no cambian la versión del producto.

SIRAP lee placas de vehículos, las asocia con personas y empresas y decide si una barrera se abre. Una placa no es
solo un número: **identifica indirectamente a una persona** y, acumulada en un historial, revela sus horarios y
movimientos. Este documento analiza los riesgos del sistema y lo que se hizo para mitigarlos.

---

## 1. Análisis de sesgos

### 1.1 Sesgos del dataset

| Sesgo | Dónde | Efecto posible |
|---|---|---|
| **Geográfico** | El detector se entrenó con placas de varios países (Roboflow), no ecuatorianas | Menor precisión con tipografías, colores o marcos propios de Ecuador |
| **Provincial** | El OCR se validó con SAVH **Guayaquil**, donde predominan las placas de Guayas (`G…`) | Rendimiento no verificado para placas de otras provincias |
| **Tipo de vehículo** | El caso original fue la entrada de camiones a una planta; el dataset de detección mezcla autos y motos (placas extranjeras de dos filas) | Las placas de camiones (sucias, a veces pintadas) pueden leerse peor; el OCR no se evaluó con motos ecuatorianas |
| **Condiciones de captura** | Imágenes mayormente diurnas y con buena iluminación | Más errores de noche, con lluvia, contraluz o placas deterioradas |
| **Estado de la placa** | Placas legibles sobrerrepresentadas tras la revisión de SAVH (472 legibles de 739) | La métrica de OCR (EMR 93,7 %) no refleja las 267 ilegibles, que deben ir a verificación manual |
| **Tamaño (distancia)** | 17,6 % de las placas de *test* son pequeñas | mAP@0.5:0.95 de 0,481 en pequeñas vs. 0,744 en grandes: los vehículos lejanos se detectan peor |

### 1.2 ¿A quién podría perjudicar?

El error que más afecta a una persona es el **falso rechazo**: un residente o proveedor autorizado cuya placa se lee
mal y queda esperando. Este error se concentra en quienes tienen **placas antiguas, dañadas, sucias o de otras
provincias**, y en vehículos de carga — es decir, con más frecuencia en conductores de vehículos más viejos o de
trabajo. El **falso acceso** (abrir a quien no debía) afecta a la seguridad de toda la comunidad.

## 2. Equidad (fairness)

SIRAP no usa atributos demográficos y no clasifica personas. La pregunta de equidad es si **el error del sistema se
reparte igual** entre grupos de vehículos/placas. Por eso:

- Se mide el mAP **por tamaño de placa** (pequeñas / medianas / grandes), que se relaciona con la distancia y el
  tipo de vehículo.
- Resultado: mAP@0.5:0.95 de 0,481 (pequeñas), 0,729 (medianas) y 0,744 (grandes). La brecha es real; en el video
  se compensa analizando a 1280 px y en la app con verificación manual.
- En la evaluación offline SAVH con la lista simulada y el umbral anterior 0,94 hubo **0 falsos autorizados** de 202
  placas no autorizadas, **1 rechazo indebido** de 197 autorizadas y 48/399 (12,0 %) casos enviados a revisión manual.
  Se aceptaron 14 lecturas erróneas (3,5 % del total), frente a 12 (3,0 %) en el escenario de estudio a 0,99. Son
  resultados por recorte con predicciones guardadas, no rendimiento punta a punta en video; 69 de las 399 etiquetas
  SAVH son sugerencias todavía no confirmadas.
- Se recomienda medir el EMR por **formato** (3 vs 4 dígitos: placas antiguas vs nuevas) y por **provincia**
  (primera letra) cuando haya datos suficientes; esa métrica de paridad queda como trabajo futuro.

**Mitigaciones implementadas**

| Mitigación | Dónde |
|---|---|
| Las placas antiguas de 3 dígitos se normalizan (`GMS-429 → GMS-0429`) y no se rechazan por formato | `src/data_processing.py` |
| Corrección de confusiones letra/dígito según la posición | `normalize_plate` |
| Una lectura dudosa **nunca** se rechaza automáticamente: va a verificación manual | `src/access_control.py` |
| Lecturas a un carácter de una placa registrada se marcan «¿quiso decir…?» en lugar de «no registrado» | `decide_access` |
| El operador puede **corregir la placa a mano** y reevaluar | Módulo Reconocimiento y Acceso |

## 3. Privacidad

### 3.1 Datos personales tratados

| Dato | ¿Personal? | Tratamiento |
|---|---|---|
| Imagen del vehículo | Sí (puede mostrar conductor, otras placas) | **No se guarda** en la base; solo se procesa en memoria |
| Placa | Sí (identifica indirectamente al propietario) | Se guarda solo cuando se registra una operación |
| Propietario registrado localmente | Sí | Nombre y datos que registra el administrador para la operación; no se requieren cédula, domicilio ni teléfono |
| Nombre devuelto por consulta pública | Sí | La API lo conserva temporalmente en memoria; la exportación enriquecida independiente puede guardarlo si se configura |
| Historial (fecha, hora, garita) | Sí (patrón de movimientos) | Solo inserción; acceso restringido al personal de la instalación |

### 3.2 Medidas

- **Minimización:** el esquema solo pide lo necesario para el control de acceso.
- **Datos ficticios** en la demo pública (archivos CSV de demostración); las imágenes reales de la garita y los registros de la
  planta **no** se publican (`data/README.md`).
- **Secretos fuera del código:** contraseñas y llaves se leen de variables de entorno; en el despliegue se guardan
  como Secrets de GitHub Actions y del Space. No se publican en el repositorio.
- **Consultas parametrizadas** (sin inyección SQL) y escape de HTML en la interfaz.
- En el Space, los secretos configurados permiten restaurar y sincronizar las tablas CSV con el repositorio privado
  `SIRAP_datos_privados`. El contenedor conserva una copia de trabajo temporal; el respaldo privado es la fuente de
  persistencia entre reinicios. En instalaciones propias, restrinja el repositorio y los permisos de acceso.
- **Versión web (producto SIRAP 1.0):** la imagen viaja por HTTPS hasta la API, se procesa en memoria y se descarta; la respuesta
  devuelve temporalmente el recorte para mostrarlo al operador. Las «lecturas de esta sesión» se guardan en la
  memoria del navegador hasta que se registran. Los CSV de datos de la demo son ficticios y se respaldan en el
  repositorio privado configurado; las imágenes reales de la garita no se publican.
- **Contraseñas y sesiones:** nunca se guardan en texto plano (PBKDF2-SHA256, 240 000 iteraciones); el token de
  sesión se guarda en el navegador y vence a las 12 h; la clave de firma (`SIRAP_JWT_SECRET`) es un *secret* del
  despliegue, no del código.

### 3.3 Cumplimiento normativo

En Ecuador aplica la **Ley Orgánica de Protección de Datos Personales (LOPDP, 2021)**, comparable al RGPD europeo.
Para un despliegue real la instalación (responsable del tratamiento) debe:

1. **Informar** con un letrero visible en la garita que existe reconocimiento automático de placas, su finalidad y
   a quién dirigirse.
2. Tener una **base legal** (interés legítimo de seguridad o consentimiento de residentes/proveedores).
3. Definir un **plazo de conservación** del historial (sugerido: 90 días, salvo incidentes) y borrarlo después.
4. Atender **derechos** de acceso, rectificación y eliminación de los titulares.
5. No ceder los datos a terceros sin base legal.

La aplicación consulta el servicio público del **SRI** para complementar la marca, el modelo y el año mostrados en
la ficha. También consulta **EcuadorLegalOnline** con la placa y la respuesta de la API puede incluir el nombre visible
asociado públicamente a ella; el panel web actual no presenta ese nombre. Las respuestas se mantienen de forma
temporal en la memoria del proceso para completar la solicitud; la exportación enriquecida independiente puede
guardar el resultado en `data/detecciones.csv` si se configura su integración de GitHub.

Estas consultas programadas no intervienen en la regla de autorización, no consultan cédula, domicilio ni teléfono y
no intentan eludir CAPTCHA o controles de acceso. El uso de información pública para esta finalidad no constituye
por sí solo una infracción ética. Aun así, placas y nombres pueden identificar personas: se informa este tratamiento,
se minimizan los campos y no se presentan resultados como verificación oficial de identidad o titularidad. Las fuentes
pueden cambiar, devolver datos incompletos o no responder; la interfaz conserva los datos locales disponibles y
muestra que la consulta externa no pudo completarse.

## 4. Transparencia y explicabilidad

- El sistema es **interpretable por diseño** en lo que decide: la regla de acceso es explícita y está documentada
  (`docs/arquitectura.md`). La parte de «caja negra» (detector y OCR) se acota con salidas verificables por un humano.
- La interfaz muestra **por qué** decidió: la caja de la placa sobre la imagen, el **recorte que leyó el OCR**, el
  texto crudo leído, la **confianza OCR** con color, la lista aplicada y el motivo (p. ej. «Confianza OCR 48 % <
  umbral 99 %»).
- El módulo **Acerca del modelo** explica el funcionamiento, las métricas y las limitaciones, y advierte cuando el
  estado del detector cargado y los errores que impiden el reconocimiento.
- No se usan SHAP/LIME porque la decisión final no depende de atributos tabulares; la evidencia visual (caja +
  recorte + probabilidad por carácter) es la explicación pertinente para un operador.

## 5. Impacto social

| Positivo | Negativo posible |
|---|---|
| Menos colas y tiempo de espera en la garita | Pérdida o cambio de tareas del personal de garita |
| Menos errores de transcripción | Sensación de vigilancia constante |
| Historial auditable ante incidentes | Uso del historial para controlar horarios de personas (p. ej. empleadas domésticas, proveedores) |
| Listas actualizadas en tiempo real | Exclusión de quien tiene placa ilegible si se elimina al guardia |

**Beneficiados:** administración, residentes, empresas. **Posibles perjudicados:** conductores con placas
deterioradas o antiguas, trabajadores sometidos a control horario no consentido y el personal de garita si el
sistema se usa para reemplazarlo en lugar de asistirlo. SIRAP se diseñó como **asistente del operador**, no como
sustituto: siempre hay un humano que confirma.

## 6. Responsabilidad (accountability)

- **Si el modelo falla, la decisión final es del operador**, que confirma cada apertura; el sistema no abre solo.
- La **apertura manual** exige motivo (≥ 10 caracteres) y confirmación explícita, y queda registrada con nombre.
- El **historial es de solo inserción**: la app no permite editar ni borrar operaciones.
- **Autenticación por usuario (SIRAP 1.0):** cada persona inicia sesión con su contraseña (guardada solo como hash
  PBKDF2-SHA256 con sal) y recibe una sesión firmada (JWT) que vence a las 12 h. Cada operación queda asociada al
  usuario autenticado, no a un nombre escrito a mano, lo que permite auditar quién abrió la barrera.
- **Permisos por rol, comprobados en el servidor:** operador (reconoce y registra), supervisor (además exporta el
  historial y consulta la administración), administrador (gestiona vehículos, listas, garitas y usuarios).
- **La interfaz no puede forzar una apertura:** antes de registrar, la API vuelve a calcular la decisión con la placa
  final; solo abre automáticamente un AUTORIZADO y la apertura manual exige motivo.
- **Responsables:** la instalación que opera SIRAP es responsable del tratamiento de datos; el equipo desarrollador
  responde por los defectos del software documentados aquí.

**Plan de monitoreo y actualización**

| Qué | Cada cuánto | Acción si empeora |
|---|---|---|
| % de lecturas enviadas a verificación manual | Semanal (Dashboard) | Revisar cámara/iluminación; reentrenar con imágenes locales |
| Aperturas manuales y su motivo | Semanal | Auditar abusos o fallas recurrentes |
| EMR sobre una muestra etiquetada de la garita | Mensual | Ajustar umbral o reentrenar |
| Vigencia de listas | Mensual | Depurar autorizaciones vencidas |

## 7. Uso dual y mal uso

El mismo sistema podría usarse para **rastrear vehículos y personas** fuera del control de acceso (vigilancia
masiva, seguimiento de una persona concreta, perfiles de movimiento, venta de datos).

**Salvaguardas**

- La app funciona **por captura en un punto de control**: no busca placas en video público ni cruza cámaras.
- Sin búsqueda de «dónde estuvo esta placa» fuera de la instalación; el historial es local.
- Imágenes no almacenadas; datos mínimos.
- Licencia y documentación declaran los usos prohibidos (abajo).

**Usos prohibidos:** vigilancia de vía pública, seguimiento de personas, decisiones automáticas sin operador,
sanciones o multas automáticas, cruce con bases de datos sin base legal, discriminación de acceso por cualquier
característica de las personas.

## 8. Limitaciones reconocidas

**No usar SIRAP**

- como único control en instalaciones de alta seguridad sin operador humano;
- para multas, sanciones o pruebas legales;
- con placas de motos o de otros países (el OCR no se evaluó con ellas);
- con cámaras que no encuadren la placa de frente o con placas que ocupen menos de ≈0,2 % del cuadro.

**Casos donde no es confiable:** noche sin iluminación infrarroja, lluvia o niebla, placas sucias, dobladas,
tapadas, con stickers o marcos que tapan caracteres, placas pintadas a mano en camiones, ángulos mayores a ≈30°,
contraluz fuerte.

**Advertencias a los usuarios** (también en la app): la confianza OCR no es una garantía; ante cualquier duda el
operador debe verificar visualmente; la versión publicada usa una barrera simulada y datos ficticios.
