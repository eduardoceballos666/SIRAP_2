# Modelos experimentales OCR SAVH

Se publican las copias originales de `ocr_afinado.onnx` (4.899.290 bytes) y `ocr_afinado.keras` (16.238.682 bytes) divididas en 3 y 9 partes binarias, respectivamente, debido a los límites del mecanismo de transferencia utilizado. Las partes no son texto base64 ni se han modificado.

Desde una copia de esta carpeta ejecutar:

```bash
python restaurar_modelos.py
```

Se reconstruyen los dos modelos y se verifican con SHA-256. No son los pesos publicados en Hugging Face ni representan un nuevo despliegue.
