---
title: SIRAP
emoji: 🚗
colorFrom: yellow
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: agpl-3.0
short_description: Reconocimiento de placas y control de acceso (YOLO11 + OCR)
---

# SIRAP · Sistema de Detección y Reconocimiento Automático de Placas

**Reconocimiento de placas y control de acceso (YOLO11 + OCR)**

**Versión del producto: SIRAP 1.0.** La API y el paquete npm del frontend usan el identificador técnico 2.0.0. El tag de GitHub `v2.0` identifica el corte del código con arquitectura FastAPI + Vue 3; no es la versión del producto. El [código fuente y la documentación](https://github.com/eduardoceballos666/SIRAP_2) se mantienen en GitHub.

## Acceso e idioma

Abre la [aplicación SIRAP](https://eduardoceballos-sirap.hf.space). Español es el idioma inicial. Para cambiar a inglés, selecciona **English** en el control **Idioma** de la pantalla de inicio de sesión o en el menú común una vez dentro. Selecciona **Español** para volver. Ambas opciones usan la misma dirección y la preferencia se conserva en ese navegador.

Las cuentas de demostración son `operador`, `supervisor` y `admin`. La contraseña se puede configurar mediante el secreto `SIRAP_DEMO_PASSWORD`. Si no se define, la API usa el valor predeterminado configurado en `api/settings.py`; para el Space público, configura explícitamente un valor propio y no publiques el valor del secreto. Los registros de demostración son ficticios y la barrera está simulada.

## Despliegue

El Space ejecuta la API FastAPI y la interfaz Vue 3 en un contenedor Docker, en el puerto 7860. El workflow [deploy-hf-space.yml](https://github.com/eduardoceballos666/SIRAP_2/blob/main/.github/workflows/deploy-hf-space.yml) publica al Space cuando hay cambios en `main` que coinciden con las rutas configuradas, y también permite iniciar el despliegue manualmente desde GitHub Actions. Los cambios solo en documentación fuera de `deploy/huggingface/`, notebooks o pruebas no activan el despliegue automático. El propio README de `deploy/huggingface/` sí coincide con una ruta incluida en el filtro del workflow, por lo que sus cambios en `main` pueden activar la publicación.

El workflow requiere los secretos `HF_TOKEN` y `SIRAP_DATA_GITHUB_TOKEN`. También puede recibir `SIRAP_JWT_SECRET` y `SIRAP_DEMO_PASSWORD` como secretos opcionales. La variable de repositorio `HF_SPACE` permite indicar el destino; si no se configura, el script de despliegue usa `eduardoceballos/sirap`. El repositorio privado de datos se establece como `eduardoceballos666/SIRAP_datos_privados`.

## Persistencia y datos consultados

### Registros de la aplicación

`SIRAP_DATA_GITHUB_TOKEN` permite a la aplicación restaurar y guardar vehículos, autorizaciones, operaciones, garitas, usuarios y credenciales en el repositorio privado `eduardoceballos666/SIRAP_datos_privados`. El almacenamiento local del Space es temporal; los CSV privados permiten conservar los registros entre reinicios. Si falta el acceso requerido al repositorio privado, el sistema no debe tratar una copia local vacía como respaldo persistente.

### Exportación enriquecida de detecciones

La exportación de detecciones usa la misma configuración privada: `SIRAP_DATA_GITHUB_TOKEN` y `SIRAP_DATA_GITHUB_REPO`. Los eventos enriquecidos se guardan en `data/processed/detecciones.csv`; no se usan las variables antiguas `GITHUB_TOKEN`, `GITHUB_DATA_REPOSITORY`, `GITHUB_DATA_BRANCH` ni `GITHUB_DATA_PATH`.

El enriquecimiento consulta datos vehiculares públicos del SRI en segundo plano y guarda el resultado en el repositorio privado. SIRAP no consulta EcuadorLegalOnline porque la información de propietario que ofrece ese servicio es de pago. El nombre del propietario, cuando aparece en la aplicación, procede del registro local.

| Dato | Uso |
|---|---|
| `SIRAP_DATA_GITHUB_TOKEN` | Secreto para leer y escribir los CSV en el repositorio privado |
| `SIRAP_DATA_GITHUB_REPO` | Repositorio privado de persistencia; el despliegue configura `eduardoceballos666/SIRAP_datos_privados` |
| `data/processed/*.csv` | Registros operativos de la aplicación |
| `data/processed/detecciones.csv` | Eventos de detección con enriquecimiento del SRI |

## Umbral y revisión humana

La configuración vigente en [config/config.yaml](https://github.com/eduardoceballos666/SIRAP_2/blob/main/config/config.yaml) establece una confianza OCR mínima de **94 %**. Las lecturas por debajo del umbral requieren verificación manual. En modo continuo de video o cámara, la interfaz espera que la misma placa alcance al menos 94 % de confianza OCR en dos cuadros aceptados dentro de 7,5 segundos antes de mostrar y registrar la decisión. Estas medidas reducen decisiones basadas en una lectura aislada; no reemplazan la revisión del operador cuando hay dudas.

La aplicación de demostración se ejecuta en CPU, sin GPU dedicada. Por eso, las mediciones de GPU del notebook no representan la latencia del Space.

## Enlaces

- **Hugging Face Space:** [SIRAP](https://huggingface.co/spaces/eduardoceballos/SIRAP)
- **Aplicación:** [eduardoceballos-sirap.hf.space](https://eduardoceballos-sirap.hf.space)
- **API interactiva:** [Swagger](https://eduardoceballos-sirap.hf.space/docs)
- **Código fuente:** [GitHub SIRAP_2](https://github.com/eduardoceballos666/SIRAP_2)
- **Manual de usuario:** [docs/manual_usuario.md](https://github.com/eduardoceballos666/SIRAP_2/blob/main/docs/manual_usuario.md)
- **Videos de presentación:** [README principal](https://github.com/eduardoceballos666/SIRAP_2#videos-de-entrega)

SIRAP 1.0 ofrece interfaz en español e inglés. La configuración del Space y su despliegue se administran desde este repositorio.

## Licencia

El código de la versión actual se distribuye bajo **GNU AGPL-3.0**; el texto completo está incluido en el archivo [`LICENSE`](https://github.com/eduardoceballos666/SIRAP_2/blob/main/LICENSE). El código fuente está disponible en [GitHub](https://github.com/eduardoceballos666/SIRAP_2). La sección 13 de la licencia contempla el acceso al código fuente correspondiente para usuarios que interactúan remotamente con versiones modificadas. Las versiones publicadas anteriormente bajo MIT conservan la licencia otorgada para esas versiones; este cambio aplica a la versión actual. Las dependencias, modelos y datos de terceros mantienen sus condiciones respectivas.
