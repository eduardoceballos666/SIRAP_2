# Artefactos pesados de SIRAP

El notebook no incrusta videos ni archivos grandes. El repositorio conserva código, CSV/JSON de resultados agregados y gráficos livianos; los medios se publican como artefactos independientes.

## Inventario

| Artefacto | Estado en esta actualización | Uso |
|---|---|---|
| `video_camiones.mp4` (video fuente completo, aprox. 459 MB) | No cargado en el repositorio ni como Release asset: la copia accesible sigue en Google Drive y la descarga directa disponible aquí rechazó el archivo por exceder el límite de transferencia. | Entrada de las secciones 6.9 y 7.2. Para una corrida sin este archivo, 6.1 usa el video público de demostración; no produce métricas de garita. |
| Videos anotados que genere la sección 6.9 | Se guardan en la carpeta temporal de Colab y no se incrustan en el notebook. | Publicar como asset de un GitHub Release cuando estén disponibles localmente. |
| Dataset SAVH y modelo YOLO11-s | Ya están versionados bajo `evidence/savh/` y `models/`. | Entradas reutilizadas desde GitHub. |

La sección 0 del notebook clona el repositorio y no monta Google Drive. Para usar la evaluación completa de garita, copia el video original a `artifacts/video_camiones.mp4` en Colab y coloca allí también las imágenes y la referencia revisada, si corresponde. No confundas el video público de demostración con el video fuente del proyecto.
