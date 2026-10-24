# SIRAP · API FastAPI + interfaz Vue en una sola imagen.
# Compatible con Hugging Face Spaces (usuario 1000, puerto 7860), Render, Railway o un servidor propio.

# 1) Compilar el frontend Vue
FROM node:22-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# 2) API + modelos
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH \
    SIRAP_API_DB=/home/user/app/data/processed/sirap_api.db
WORKDIR /home/user/app

COPY --chown=user requirements.txt ./
COPY --chown=user api/requirements.txt api/requirements.txt
RUN pip install --user -r api/requirements.txt
# Descarga el OCR (≈5 MB) durante la construcción para que el primer reconocimiento sea inmediato.
RUN python -c "from fast_plate_ocr import LicensePlateRecognizer as R; R('cct-s-v2-global-model')"

COPY --chown=user . .
COPY --chown=user --from=frontend /app/frontend/dist frontend/dist
RUN mkdir -p data/processed

EXPOSE 7860
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
