"""Modelos de SIRAP: detector de placas (YOLO11-s), lector OCR (fast-plate-ocr) y pipeline ALPR.

Flujo de una imagen::

    imagen ──► PlateDetector ──► cajas de placa ──► recorte ──► PlateReader (OCR)
                                                               └─► normalize_plate ──► Recognition

* **Detector.** YOLO11-s entrenado en el notebook ``notebooks/SIRAP_backend.ipynb`` (sección 3.2).
  Se carga en este orden: ``models/best_model.onnx`` con ONNX Runtime (sin PyTorch: es lo que usa
  Streamlit Cloud), ``models/best_model.pt`` con Ultralytics y, si no hay pesos, un localizador
  clásico con OpenCV que la interfaz marca como *respaldo*.
* **OCR.** ``fast-plate-ocr`` con ``cct-s-v2-global-model`` (≈5 MB, corre en CPU).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from src.data_processing import (DEFAULT_PATTERNS, clean_text, crop_with_margin, letterbox,
                                 normalize_plate)
from src.utils import get_logger, load_config, load_json, resolve_path, timer

logger = get_logger("sirap.model")


# --------------------------------------------------------------------------------------------
# Resultados
# --------------------------------------------------------------------------------------------

@dataclass
class Detection:
    """Una caja de placa detectada en la imagen."""

    box: tuple[float, float, float, float]  # x1, y1, x2, y2 en píxeles de la imagen original
    confidence: float

    @property
    def area(self) -> float:
        x1, y1, x2, y2 = self.box
        return max(0.0, x2 - x1) * max(0.0, y2 - y1)


@dataclass
class Recognition:
    """Resultado completo del reconocimiento de una imagen."""

    plate: str | None                       # placa normalizada XXX-0000 (None si no es válida)
    plate_raw: str = ""                     # texto tal como lo devolvió el OCR
    ocr_confidence: float = 0.0             # menor probabilidad entre los caracteres (0–1), como en el notebook
    ocr_mean_confidence: float = 0.0        # promedio de la probabilidad por carácter (0–1)
    det_confidence: float = 0.0             # confianza del detector (0–1)
    box: tuple[float, float, float, float] | None = None
    crop: np.ndarray | None = field(default=None, repr=False)
    detector: str = ""                      # "YOLO11-s (ONNX)", "YOLO11-s (PyTorch)" o "OpenCV (respaldo)"
    timings_ms: dict[str, float] = field(default_factory=dict)
    candidates: int = 0                     # cajas evaluadas

    @property
    def found(self) -> bool:
        """``True`` si se encontró y leyó una placa con formato válido."""
        return self.plate is not None

    def as_dict(self) -> dict[str, Any]:
        """Versión serializable (sin el recorte) para registrar o exportar."""
        return {
            "plate": self.plate, "plate_raw": self.plate_raw,
            "ocr_confidence": round(self.ocr_confidence, 4),
            "ocr_mean_confidence": round(self.ocr_mean_confidence, 4),
            "det_confidence": round(self.det_confidence, 4),
            "box": [round(v, 1) for v in self.box] if self.box else None,
            "detector": self.detector, "timings_ms": {k: round(v, 1) for k, v in self.timings_ms.items()},
        }


# --------------------------------------------------------------------------------------------
# Detector
# --------------------------------------------------------------------------------------------

def _nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float) -> list[int]:
    """Supresión de no máximos (NMS) simple en NumPy. ``boxes`` en formato x1, y1, x2, y2."""
    order = scores.argsort()[::-1]
    keep: list[int] = []
    while order.size:
        i = int(order[0])
        keep.append(i)
        if order.size == 1:
            break
        rest = order[1:]
        xx1 = np.maximum(boxes[i, 0], boxes[rest, 0])
        yy1 = np.maximum(boxes[i, 1], boxes[rest, 1])
        xx2 = np.minimum(boxes[i, 2], boxes[rest, 2])
        yy2 = np.minimum(boxes[i, 3], boxes[rest, 3])
        inter = np.clip(xx2 - xx1, 0, None) * np.clip(yy2 - yy1, 0, None)
        area_i = (boxes[i, 2] - boxes[i, 0]) * (boxes[i, 3] - boxes[i, 1])
        area_r = (boxes[rest, 2] - boxes[rest, 0]) * (boxes[rest, 3] - boxes[rest, 1])
        iou = inter / np.maximum(area_i + area_r - inter, 1e-9)
        order = rest[iou <= iou_threshold]
    return keep


class PlateDetector:
    """Localiza placas en una imagen RGB.

    Args:
        onnx_path: pesos exportados a ONNX (``yolo export format=onnx``).
        pt_path: pesos ``best.pt`` de Ultralytics.
        imgsz: tamaño de inferencia (lado del cuadrado).
        conf: confianza mínima de una caja.
        iou: umbral de solapamiento del NMS.
        allow_fallback: si no hay pesos, usar el localizador clásico de OpenCV.
    """

    def __init__(self, onnx_path: str | Path | None = None, pt_path: str | Path | None = None,
                 imgsz: int = 640, conf: float = 0.25, iou: float = 0.7, allow_fallback: bool = False):
        self.imgsz, self.conf, self.iou = int(imgsz), float(conf), float(iou)
        self.backend = "none"
        self.name = "sin detector"
        self._session = None
        self._yolo = None
        onnx_file = resolve_path(onnx_path) if onnx_path else None
        pt_file = resolve_path(pt_path) if pt_path else None

        if onnx_file and onnx_file.exists():
            try:
                import onnxruntime as ort

                self._session = ort.InferenceSession(str(onnx_file), providers=["CPUExecutionProvider"])
                self._input_name = self._session.get_inputs()[0].name
                shape = self._session.get_inputs()[0].shape
                if isinstance(shape[-1], int):  # modelo exportado con tamaño fijo
                    self.imgsz = int(shape[-1])
                self.backend, self.name = "onnx", "YOLO11-s (ONNX)"
            except Exception as exc:  # noqa: BLE001
                logger.error("No se pudo cargar el ONNX %s: %s", onnx_file, exc)
        if self.backend == "none" and pt_file and pt_file.exists():
            try:
                from ultralytics import YOLO  # type: ignore

                self._yolo = YOLO(str(pt_file))
                self.backend, self.name = "ultralytics", "YOLO11-s (PyTorch)"
            except Exception as exc:  # noqa: BLE001
                logger.error("No se pudo cargar %s con Ultralytics: %s", pt_file, exc)
        if self.backend == "none" and allow_fallback:
            self.backend, self.name = "opencv", "OpenCV (respaldo)"
            logger.warning("No hay pesos de YOLO11 en models/: se usa el localizador clásico de OpenCV.")

    @property
    def is_model(self) -> bool:
        """``True`` si se está usando el detector entrenado (no el respaldo)."""
        return self.backend in ("onnx", "ultralytics")

    def detect(self, image: np.ndarray, max_detections: int = 5) -> list[Detection]:
        """Devuelve las cajas de placa ordenadas de mayor a menor confianza."""
        if self.backend == "onnx":
            detections = self._detect_onnx(image)
        elif self.backend == "ultralytics":
            detections = self._detect_ultralytics(image)
        elif self.backend == "opencv":
            detections = self._detect_opencv(image)
        else:
            raise RuntimeError("No hay detector disponible: copia los pesos en models/best_model.onnx.")
        detections.sort(key=lambda d: d.confidence, reverse=True)
        return detections[:max_detections]

    # -- YOLO11 en ONNX Runtime -------------------------------------------------------------
    def _detect_onnx(self, image: np.ndarray) -> list[Detection]:
        canvas, scale, (pad_x, pad_y) = letterbox(image, self.imgsz)
        tensor = canvas.astype(np.float32).transpose(2, 0, 1)[None] / 255.0
        output = self._session.run(None, {self._input_name: tensor})[0]  # (1, 4 + clases, N)
        preds = np.squeeze(output, 0)
        if preds.shape[0] < preds.shape[1]:
            preds = preds.T  # (N, 4 + clases)
        scores = preds[:, 4:].max(axis=1)
        mask = scores >= self.conf
        if not mask.any():
            return []
        preds, scores = preds[mask], scores[mask]
        cx, cy, w, h = preds[:, 0], preds[:, 1], preds[:, 2], preds[:, 3]
        boxes = np.stack([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], axis=1)
        keep = _nms(boxes, scores, self.iou)
        height, width = image.shape[:2]
        result = []
        for i in keep:
            x1, y1, x2, y2 = boxes[i]
            x1, x2 = (np.array([x1, x2]) - pad_x) / scale
            y1, y2 = (np.array([y1, y2]) - pad_y) / scale
            result.append(Detection((float(np.clip(x1, 0, width)), float(np.clip(y1, 0, height)),
                                     float(np.clip(x2, 0, width)), float(np.clip(y2, 0, height))),
                                    float(scores[i])))
        return result

    # -- YOLO11 con Ultralytics -------------------------------------------------------------
    def _detect_ultralytics(self, image: np.ndarray) -> list[Detection]:
        results = self._yolo.predict(image[..., ::-1], imgsz=self.imgsz, conf=self.conf, iou=self.iou,
                                     verbose=False)
        boxes = results[0].boxes
        return [Detection(tuple(float(v) for v in xyxy), float(c))
                for xyxy, c in zip(boxes.xyxy.cpu().numpy(), boxes.conf.cpu().numpy())]

    # -- Respaldo clásico (OpenCV) ----------------------------------------------------------
    @staticmethod
    def _detect_opencv(image: np.ndarray) -> list[Detection]:
        """Busca regiones rectangulares claras con proporción de placa (≈2:1 a 6:1).

        No es un modelo entrenado: sirve solo para que la interfaz funcione sin pesos. La
        "confianza" es un puntaje heurístico de forma y contraste, no una probabilidad.
        """
        import cv2

        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        height, width = gray.shape
        blur = cv2.bilateralFilter(gray, 9, 50, 50)
        candidates: list[Detection] = []
        for block in (31, 51):
            thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY, block, -5)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3)))
            contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if w < 40 or h < 12 or w * h < 0.0008 * width * height or w * h > 0.2 * width * height:
                    continue
                ratio = w / float(h)
                if not 1.8 <= ratio <= 6.5:
                    continue
                roi = gray[y:y + h, x:x + w]
                fill = cv2.contourArea(contour) / float(w * h)
                contrast = float(roi.std()) / 64.0
                edges = cv2.Canny(roi, 80, 200).mean() / 255.0
                score = 0.4 * min(fill, 1.0) + 0.3 * min(contrast, 1.0) + 0.3 * min(edges * 4, 1.0)
                candidates.append(Detection((float(x), float(y), float(x + w), float(y + h)), float(score)))
        if not candidates:
            return []
        boxes = np.array([c.box for c in candidates], dtype=np.float32)
        scores = np.array([c.confidence for c in candidates], dtype=np.float32)
        return [candidates[i] for i in _nms(boxes, scores, 0.3)]


# --------------------------------------------------------------------------------------------
# OCR
# --------------------------------------------------------------------------------------------

class PlateReader:
    """Lee el texto de un recorte de placa con fast-plate-ocr.

    Args:
        model_name: modelo del hub de fast-plate-ocr (por defecto ``cct-s-v2-global-model``).
        device: ``"cpu"``, ``"cuda"`` o ``"auto"``.
        onnx_path, plate_config_path: modelo afinado propio. Si ambos archivos existen se usan en lugar
            del modelo del hub.
    """

    def __init__(self, model_name: str = "cct-s-v2-global-model", device: str = "cpu",
                 onnx_path: str | Path | None = None, plate_config_path: str | Path | None = None):
        from fast_plate_ocr import LicensePlateRecognizer  # importación diferida: descarga el modelo

        onnx_file = resolve_path(onnx_path) if onnx_path else None
        config_file = resolve_path(plate_config_path) if plate_config_path else None
        if onnx_file and config_file and onnx_file.exists() and config_file.exists():
            # OCR afinado con placas ecuatorianas (notebooks/06_afinamiento_ocr.ipynb)
            self.model_name = f"{model_name} afinado ({onnx_file.name})"
            self._model = LicensePlateRecognizer(onnx_model_path=onnx_file, plate_config_path=config_file,
                                                 device=device)
        else:
            self.model_name = model_name
            self._model = LicensePlateRecognizer(model_name, device=device)

    def read(self, crop: np.ndarray) -> tuple[str, float, float]:
        """Lee un recorte RGB.

        Returns:
            ``(texto, confianza, confianza_promedio)``. La confianza es la **menor** probabilidad entre los
            caracteres leídos (sin el relleno), como ``plate_confidence`` en el notebook.
        """
        if crop is None or crop.size == 0:
            return "", 0.0, 0.0
        prediction = self._model.run(np.ascontiguousarray(crop), return_confidence=True)[0]
        text = clean_text(prediction.plate)
        probs = np.asarray(prediction.char_probs, dtype=np.float32).ravel()
        used = probs[:max(len(text), 1)]
        # Confianza de la placa = la menor probabilidad entre sus caracteres (plate_confidence del notebook).
        return text, float(used.min()), float(used.mean())


# --------------------------------------------------------------------------------------------
# Pipeline completo
# --------------------------------------------------------------------------------------------

class ALPRPipeline:
    """Detección + OCR + normalización para una imagen.

    Se lee cada caja candidata (hasta ``max_candidates``) y se queda con la mejor lectura válida.
    """

    def __init__(self, detector: PlateDetector, reader: PlateReader,
                 patterns: Sequence[Sequence[int]] = DEFAULT_PATTERNS, margin: float = 0.06,
                 max_candidates: int = 5):
        self.detector, self.reader = detector, reader
        self.patterns, self.margin, self.max_candidates = patterns, margin, max_candidates

    @classmethod
    def from_config(cls, config: dict[str, Any] | None = None) -> "ALPRPipeline":
        """Crea el pipeline con ``config/config.yaml`` (umbral calibrado si está guardado)."""
        cfg = config or load_config()
        det_cfg, ocr_cfg = cfg["detector"], cfg["ocr"]
        calibrated = load_json("results/metrics/umbrales.json") or {}
        conf = float(calibrated.get("YOLO11", {}).get("conf_track", det_cfg.get("conf_minima", 0.25)))
        detector = PlateDetector(det_cfg.get("pesos_onnx"), det_cfg.get("pesos_pt"),
                                 imgsz=det_cfg.get("imgsz_inferencia", 640), conf=conf,
                                 iou=det_cfg.get("iou_nms", 0.7),
                                 allow_fallback=det_cfg.get("permitir_respaldo_opencv", True))
        reader = PlateReader(ocr_cfg.get("modelo", "cct-s-v2-global-model"), ocr_cfg.get("dispositivo", "cpu"),
                             ocr_cfg.get("onnx_afinado"), ocr_cfg.get("plate_config_afinado"))
        patterns = [tuple(p) for p in cfg.get("placas", {}).get("patrones", DEFAULT_PATTERNS)]
        return cls(detector, reader, patterns, det_cfg.get("margen_recorte", 0.06))

    def recognize(self, image: np.ndarray) -> Recognition:
        """Reconoce la placa principal de ``image`` (RGB).

        Returns:
            Un ``Recognition``; ``found`` es ``False`` si no se detectó o no se pudo leer una placa válida.
        """
        timings: dict[str, float] = {}
        with timer() as t_det:
            detections = self.detector.detect(image, self.max_candidates)
        timings["deteccion"] = t_det["ms"]
        best: Recognition | None = None
        with timer() as t_ocr:
            for det in detections:
                crop = crop_with_margin(image, det.box, self.margin)
                raw, conf, mean_conf = self.reader.read(crop)
                plate = normalize_plate(raw, self.patterns)
                candidate = Recognition(plate, raw, conf, mean_conf, det.confidence, det.box, crop,
                                        self.detector.name)
                # Prioridad: lectura válida > confianza OCR > confianza del detector.
                key = (candidate.found, candidate.ocr_confidence, candidate.det_confidence)
                if best is None or key > (best.found, best.ocr_confidence, best.det_confidence):
                    best = candidate
                if self.detector.is_model and candidate.found:
                    break  # con el modelo entrenado la primera caja válida es la de mayor confianza
        timings["ocr"] = t_ocr["ms"]
        timings["total"] = timings["deteccion"] + timings["ocr"]
        result = best or Recognition(None, detector=self.detector.name)
        result.timings_ms, result.candidates = timings, len(detections)
        logger.info("Reconocimiento: placa=%s raw=%s conf=%.3f det=%s %.0f ms", result.plate,
                    result.plate_raw, result.ocr_confidence, self.detector.name, timings["total"])
        return result
