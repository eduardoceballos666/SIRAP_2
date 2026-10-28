---
title: SIRAP
emoji: 🚧
colorFrom: yellow
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Reconocimiento de placas y control de acceso (YOLO11 + OCR)
---

# SIRAP · Sistema de Detección y Reconocimiento Automático de Placas

Versión web (API FastAPI + interfaz Vue 3). Código fuente y documentación:
https://github.com/eduardoceballos666/SIRAP_2

Usuarios de demostración: `operador`, `supervisor` y `admin`; contraseña inicial `sirap2026`. Los registros contienen
**datos ficticios** y la barrera es **simulada**. Los secretos están configurados para respaldar tablas CSV en
`SIRAP_datos_privados`. El workflow publica automáticamente al cambiar rutas de aplicación incluidas en sus filtros
de `main`; cambios solo en documentación, notebooks o pruebas no activan el despliegue. También se puede iniciar
manualmente desde GitHub Actions.

## Persistencia y consultas de datos

### A. Respaldo de las tablas CSV de la aplicación

`SIRAP_DATA_GITHUB_TOKEN` es el secreto que la API usa para **restaurar y guardar** vehículos, listas, usuarios,
garitas e historial en `eduardoceballos666/SIRAP_datos_privados`. `SIRAP_DATA_GITHUB_REPO` indica ese repositorio;
si no se define, el código usa ese repositorio por defecto. En el despliegue actual, el flujo de GitHub Actions
valida el token y configura ambos valores como secretos del Space. Esta es la integración que mantiene los datos
principales después de reiniciar el contenedor.

La ficha de la aplicación consulta el servicio público del SRI para completar marca, modelo y año. La API también
consulta EcuadorLegalOnline con la placa; puede recibir el nombre visible asociado públicamente, aunque el panel actual
no lo muestra. Las respuestas complementan los datos locales y no intervienen en la decisión de acceso. Se mantienen
temporalmente en memoria durante la consulta. La exportación enriquecida independiente puede guardar resultados en
`data/detecciones.csv` solo si se configura con sus variables propias. No se consultan cédula, domicilio ni teléfono;
si una fuente no responde o requiere CAPTCHA, no se eluden sus controles.

### B. Exportación enriquecida de detecciones

`GITHUB_TOKEN` y `GITHUB_DATA_REPOSITORY` pertenecen a otro módulo: escriben eventos de detección enriquecidos
en `data/detecciones.csv` (con variables opcionales `GITHUB_DATA_BRANCH` y `GITHUB_DATA_PATH`). No restauran ni
respaldan las tablas principales de la aplicación y no sustituyen `SIRAP_DATA_GITHUB_TOKEN`. No configures un token
de una integración como si fuera el de la otra: cada una requiere permiso de escritura en su propio repositorio
privado de destino.

| Integración | Variables | Qué guarda |
|---|---|---|
| Persistencia de la aplicación | `SIRAP_DATA_GITHUB_TOKEN`, `SIRAP_DATA_GITHUB_REPO` | CSV operativos en `SIRAP_datos_privados`; restaura al iniciar y sincroniza cambios |
| Exportación enriquecida | `GITHUB_TOKEN`, `GITHUB_DATA_REPOSITORY` (opcionales: `GITHUB_DATA_BRANCH`, `GITHUB_DATA_PATH`) | Eventos de detección enriquecidos en `data/detecciones.csv` |

## Umbral operativo OCR

La aplicación usa un umbral de confianza OCR de **99 %**. Las lecturas por debajo pasan a verificación manual.
