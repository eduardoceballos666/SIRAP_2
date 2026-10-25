"""SIRAP – Sistema de Detección y Reconocimiento Automático de Placas.

Módulos:
    data_processing  validación de imágenes, recortes y normalización de placas
    model            detector YOLO11-s, OCR fast-plate-ocr y pipeline ALPR
    access_control   regla de decisión y controlador de barrera
    storage           archivos CSV locales: vehículos, listas e historial
    train            entrenamiento y exportación del detector
    evaluate         métricas del detector y del sistema completo
    utils            configuración, secretos y logging
"""

__version__ = "1.0.0"
