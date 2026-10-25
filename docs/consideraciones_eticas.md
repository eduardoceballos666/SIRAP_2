# Consideraciones éticas – SIRAP 2

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
- En la regla de decisión evaluada con SAVH (lista simulada, 399 imágenes): **0 falsos autorizados** de 202 y
  **1 rechazo indebido** de 197, con 15,5 % a verificación manual (umbral OCR 0,99).
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
| Propietario | Sí | Nombre y **un** contacto (minimización); sin cédula, dirección ni teléfono obligatorios |
| Historial (fecha, hora, garita) | Sí (patrón de movimientos) | Solo inserción; acceso restringido al personal de la instalación |

### 3.2 Medidas

- **Minimización:** el esquema solo pide lo necesario para el control de acceso.
- **Datos ficticios** en la demo pública (archivos CSV de demostración); las imágenes reales de la garita y los registros de la
  planta **no** se publican (`data/README.md`).
- **Secretos fuera del código:** DSN, PIN y llaves se leen de variables de entorno o `st.secrets`. Una versión
  antigua del notebook tenía llaves de Roboflow en celdas; se revocaron y se pasó a *Secrets*.
- **Consultas parametrizadas** (sin inyección SQL) y escape de HTML en la interfaz.
- El almacenamiento local de la demo es temporal; proteja los archivos CSV con permisos de acceso y use HTTPS para la barrera.
- **Versión web (SIRAP 2):** la imagen viaja por HTTPS hasta la API, se procesa en memoria y se descarta; la respuesta
  solo devuelve el recorte de la placa. Las «lecturas de esta sesión» se guardan únicamente en la memoria del
  navegador del operador (no en el servidor) hasta que se registran. La demo pública reinicia su base en cada
  reinicio del servidor y solo contiene datos ficticios.
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

La integración con **SRI / ANT** (consulta de datos del vehículo) solo debe hacerse con acceso autorizado y para la
finalidad declarada. El notebook de investigación consulta además el **nombre público del propietario** en un sitio
de terceros; esa consulta no está en la app, extrae solo el campo gratuito «Nombre» (sin cédula, dirección ni
teléfono) y, para un despliegue real, debe reemplazarse por un acceso formal o eliminarse.

## 4. Transparencia y explicabilidad

- El sistema es **interpretable por diseño** en lo que decide: la regla de acceso es explícita y está documentada
  (`docs/arquitectura.md`). La parte de «caja negra» (detector y OCR) se acota con salidas verificables por un humano.
- La interfaz muestra **por qué** decidió: la caja de la placa sobre la imagen, el **recorte que leyó el OCR**, el
  texto crudo leído, la **confianza OCR** con color, la lista aplicada y el motivo (p. ej. «Confianza OCR 48 % <
  umbral 85 %»).
- El módulo **Acerca del modelo** explica el funcionamiento, las métricas y las limitaciones, y advierte cuando el
  detector entrenado no está cargado («Detector de respaldo activo»).
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
- **Autenticación por usuario (SIRAP 2):** cada persona inicia sesión con su contraseña (guardada solo como hash
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
