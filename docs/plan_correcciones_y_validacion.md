# Plan de corrección y cierre de brechas de SIRAP_2

**Fecha:** 14 de noviembre de 2026  
**Estado:** cambios de código y documentación preparados en la rama `fix/sirap2-security-evaluation-20261114`. No se ha desplegado la rama ni se han cambiado datos privados, secretos o etiquetas de evaluación.

## Evidencia vigente

La meta de exactitud de lectura del 80 % para el sistema completo no se cumple con los resultados publicados:

- **Imágenes de garita:** el informe registra 8/21 (38,1 %). Una salida guardada distinta registra 9/21 (42,9 %), sin fecha ni ID de corrida; no se deben combinar.
- **Cinco clips:** 3/5 (60 %) coincidieron exactamente. En dos clips se confirmó una lectura equivocada con OCR ≥0,94 y la regla de dos cuadros. Esto mide confirmación de lectura, no apertura real de barrera.
- **Video completo:** la reejecución más reciente obtuvo 18/30 (60 %). De 51 lecturas, 21 no tienen referencia; dos pasadas dudosas siguen excluidas. Se observaron dos falsas autorizaciones entre los 30 casos comparables, por lo que la tasa del video completo no se puede estimar. El 17/24 (70,83 %) es de una corrida anterior.
- **OCR de recortes:** el 388/398 (97,49 %) no es una validación independiente: algunas sugerencias OCR estuvieron visibles al revisar etiquetas y 14 desacuerdos se aceptaron con esa sugerencia. El piloto visual de 84 imágenes conserva 13 discrepancias sin adjudicar. El holdout más independiente obtuvo 42/57 (73,7 %), sin doble adjudicación y con muestra pequeña.

El umbral operativo de la aplicación es 0,94. El 0,99 corresponde a comparaciones offline previas. Una métrica de recortes no debe presentarse como exactitud punta a punta.

## Cambios preparados en el código

- El endpoint de alta solo crea vehículos pendientes. Rechaza explícitamente solicitudes antiguas que intenten autorizar en el mismo registro.
- Solo un Administrador puede añadir una placa a la lista blanca. La misma cuenta que creó la ficha no puede aprobarla, incluso mediante autorización masiva. Esta separación distingue cuentas técnicas, no acredita que correspondan a personas diferentes; la organización debe asignar una cuenta individual a cada persona.
- El backend conserva la cuenta registrante también cuando el Administrador crea un vehículo desde Administración. La interfaz ya no ofrece autorización al registrar. En filas históricas donde `registrado_por` esté vacío no se puede comprobar retrospectivamente quién creó la ficha; validar esos casos antes de una nueva autorización.
- Producción deja de usar una contraseña compartida o predeterminada. El despliegue exige una clave JWT configurada y hashes individuales para todas las cuentas activas; también elimina el secreto heredado de contraseña compartida del Space. Las contraseñas nuevas y restablecidas requieren 15 caracteres.
- Las guías ya separan métricas de componentes y del sistema completo, describen las imágenes y video de evaluación que sí se publican y dejan de llamar inmutable a la auditoría CSV.

Estos cambios requieren aprobación e integración en `main`; el workflow de despliegue se ejecuta desde `main`, no desde esta rama.

## Trabajo pendiente para cerrar la evaluación

### 1. Anotación ciega y evaluación de extremo a extremo

- Adjudicar las 13 discrepancias del piloto y completar la referencia de las 21 lecturas del video que hoy no tienen etiqueta.
- Revisar las dos pasadas excluidas con dos anotadores que no vean la salida del OCR; documentar desacuerdos y resolverlos antes de congelar la referencia.
- Separar calibración y prueba final por vehículo o pasada. Congelar el umbral y la regla de decisión antes de abrir el conjunto final.
- Reportar, por imagen, clip y pasada, coincidencia exacta, cobertura, omisiones, falsos rechazos y falsas autorizaciones con numeradores y denominadores explícitos. Incluir intervalo de confianza del 95 %.
- Repetir la medición después de congelar las etiquetas; no usar las sugerencias del OCR para adjudicar la referencia.

### 2. Detector en el dominio de garita

El test principal del detector usa 10.125 imágenes de varias escenas y países; solo nueve son imágenes sin placa y una está en test. La precisión global publicada sí refleja falsos positivos dentro de ese test, pero no estima las falsas detecciones en la garita.

- Reunir un conjunto de garita con negativos difíciles: sin vehículo, sin placa, reflejos, letreros, placas parciales, lluvia, noche, contraluz y objetos parecidos a una placa.
- Asegurar que imágenes del mismo vehículo, secuencia o pasada no queden repartidas entre calibración y test.
- Informar falsos positivos por imagen y métricas de detección de placas con conteos por condición. Mantener el video final separado para la evaluación del sistema completo.

### 3. Entrenamiento y comparación de la búsqueda

- Los 24 trials de Optuna usaron 30 % de entrenamiento y 10 épocas; el mejor `lr0=0,000163` quedó cerca del borde inferior probado (0,0001).
- La búsqueda fijó AdamW y `lr0=0,002`; el registro de los pesos base indica `optimizer="auto (AdamW)"`. Repetir base y candidato con el mismo dataset, optimizer, resolución, semillas y presupuesto antes de atribuir una mejora.
- Revisar curvas de pérdida y validación. Que el mejor checkpoint sea de la época 40 y que no se activara early stopping no prueba que no convergió; decidir si extender épocas a partir de esas curvas.
- Seleccionar hiperparámetros y umbrales usando solo validación. Evaluar el test reservado una vez con el protocolo congelado.

### 4. Escenarios operativos críticos

Añadir y ejecutar pruebas para: usuario sin rol suficiente; alta nueva pendiente; rechazo de autoaprobación individual y masiva; expiración/revocación de autorización; confianza baja o lecturas contradictorias; detector sin placa; duplicados por reintento; CSV o repositorio privado indisponible; y fallo/estado incierto de barrera. El registro no debe abrir una barrera cuando la decisión o la persistencia no se pueden confirmar.

### 5. Secretos y cuentas

- Configurar `SIRAP_JWT_SECRET` en los secretos de GitHub Actions con una cadena aleatoria única de al menos 32 caracteres; el workflow fallará si falta.
- Restablecer individualmente las contraseñas de todas las cuentas activas en el CSV privado. Cambiar una variable de entorno no reemplaza los hashes ya guardados.
- No volver a usar la antigua clave compartida de demostración: apareció en configuración pública y debe tratarse como comprometida. No guardar secretos en archivos del repositorio.
- Verificar permisos del token de datos: limitarlo al repositorio privado y a lectura/escritura de contenidos que el despliegue requiera.

### 6. Auditoría e integridad de datos

El almacenamiento operativo actual son CSV privados. El backend actualiza filas existentes para reflejar estado de barrera y autorización; el historial de commits de GitHub no garantiza que los eventos sean inmutables.

Para producción, migrar a una base de datos persistente con eventos de auditoría de solo anexado: actor, hora, entidad, acción, valores anteriores/nuevos, motivo y resultado. Restringir actualización/borrado de eventos, conservar respaldos independientes y verificar restauración. La infraestructura y sus credenciales no están configuradas en esta rama.

### 7. Publicación de datos y guías

`data/README.md` indica autorización escrita para las imágenes y el video de garita publicados. Confirmar que la autorización cubra las imágenes, placas y referencias que están en GitHub y en el Release. Revisar también la licencia del dataset SAVH antes de redistribuirlo: su ficha consultada no muestra licencia para el archivo concreto. Al integrar el cambio de interfaz, volver a generar las capturas y las ediciones Word/PDF del manual para que no muestren la casilla de autorización retirada.

## Criterios antes de declarar la meta alcanzada

- Una evaluación independiente y congelada de extremo a extremo obtiene al menos 80 % de exactitud; se informa su intervalo de confianza, cobertura y casos omitidos.
- La tasa de falsas autorizaciones tiene una referencia completa y un denominador válido; las lecturas sin referencia no se contabilizan como aciertos.
- La tasa de falsas detecciones se mide con negativos representativos de garita.
- Pasan las pruebas de roles, aprobaciones distintas, fallos de almacenamiento y escenarios operativos.
- Las credenciales existentes están rotadas individualmente y la auditoría de producción no depende de archivos CSV editables.

Hasta cerrar esos puntos, la evidencia no permite afirmar que SIRAP cumpla la meta del 80 % ni usar el reconocimiento como único control de acceso.
