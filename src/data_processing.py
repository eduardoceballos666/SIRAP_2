"""Procesamiento de datos de SIRAP: validación de imágenes, recortes y normalización de placas.

La normalización es la misma del notebook de backend (``notebooks/SIRAP_backend.ipynb``,
sección 5, celda «Normalización de placas»), validada con las placas reales de SAVH Guayaquil:

* Una placa válida tiene **3 letras + 4 dígitos** (formato actual) o **3 letras + 3 dígitos**
  (formato antiguo).
* Para decidir, guardar y mostrar, toda placa válida se escribe ``XXX-0000``. A las placas
  antiguas de 3 dígitos se les antepone un 0: ``GMS-429`` → ``GMS-0429``.
* El OCR confunde caracteres parecidos (``0``/``O``, ``1``/``I``, ``8``/``B``…). Como la posición
  indica si el carácter debe ser letra o dígito, se corrigen esas confusiones por posición, con
  un máximo de 2 cambios (en SAVH ninguna lectura que necesitó 3 cambios era correcta).
* La placa se busca en el texto por tramos entre separadores (``"ECUADOR GMS 429"`` → ``GMS-0429``).
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

# --------------------------------------------------------------------------------------------
# Placas
# --------------------------------------------------------------------------------------------

#: Patrones válidos (letras, dígitos) en orden de frecuencia.
DEFAULT_PATTERNS: tuple[tuple[int, int], ...] = ((3, 4), (3, 3))

CONFUSIONS_TO_LETTER = {"0": "O", "1": "I", "5": "S", "6": "G", "8": "B"}  # dígito leído donde va una letra
CONFUSIONS_TO_DIGIT = {"O": "0", "D": "0", "Q": "0", "I": "1", "Z": "2", "B": "8"}  # letra leída donde va un dígito
SYMBOLS_TO_CHAR = {"|": "1", "$": "S"}
SEPARATORS = " \t\r\n-‐‑‒–—_.·•:,;+\"'`*()[]{}<>"
MAX_CORRECTIONS = 2
PLATE_HEADER = "ECUADOR"  # leyenda impresa sobre la placa
_SEGMENT = re.compile("[^" + re.escape(SEPARATORS) + "]+")
_FORMATTED_RE = re.compile(r"^[A-Z]{3}-\d{4}$")


def clean_text(raw: str | None) -> str:
    """Mayúsculas y solo letras y dígitos: ``'gba-1234'`` → ``'GBA1234'``."""
    if not raw:
        return ""
    return re.sub(r"[^A-Z0-9]", "", str(raw).upper())


def _is_plate_header(segment: str) -> bool:
    """``ECUADOR`` y lecturas aproximadas (``EQUADOR``): solo letras y a 3 cambios o menos."""
    if not (len(segment) >= 5 and segment.isascii() and segment.isalpha()):
        return False
    return plate_distance(segment, PLATE_HEADER) <= 3


def _as_plate(candidate: str, patterns: Sequence[Sequence[int]]) -> tuple[str, int, int] | None:
    """``(placa, cambios, n_letras)`` si el candidato tiene formato de placa tras corregir por posición."""
    for n_letters, n_digits in patterns:
        n_letters, n_digits = int(n_letters), int(n_digits)
        if len(candidate) != n_letters + n_digits:
            continue
        letters = "".join(CONFUSIONS_TO_LETTER.get(c, c) for c in candidate[:n_letters])
        digits = "".join(CONFUSIONS_TO_DIGIT.get(c, c) for c in candidate[n_letters:])
        plate = letters + digits
        changes = sum(a != b for a, b in zip(plate, candidate))
        if changes <= MAX_CORRECTIONS and re.fullmatch(f"[A-Z]{{{n_letters}}}[0-9]{{{n_digits}}}", plate):
            return plate, changes, n_letters
    return None


def find_plate(raw: str | None, patterns: Sequence[Sequence[int]] = DEFAULT_PATTERNS) -> tuple[str, bool, int]:
    """Busca la placa en el texto del OCR → ``(placa sin guion, formato válido, cambios)``.

    Prueba cada tramo entre separadores y las uniones de 2 o 3 tramos seguidos (``'GBA 1234'``),
    sin la leyenda ECUADOR. Gana el candidato que valida con menos cambios y, a igualdad, el primero.
    """
    text = str(raw or "").upper()
    segments = ["".join(SYMBOLS_TO_CHAR.get(c, c) for c in m.group()) for m in _SEGMENT.finditer(text)]
    segments = [s for s in segments if not _is_plate_header(s)]
    best: tuple[str, int] | None = None
    for i in range(len(segments)):
        for j in range(i + 1, min(i + 3, len(segments)) + 1):
            found = _as_plate("".join(segments[i:j]), patterns)
            if found and (best is None or found[1] < best[1]):
                best = (found[0], found[1])
    if best:
        return best[0], True, best[1]
    return clean_text("".join(segments)), False, 0


def format_plate(text: str) -> str:
    """Formato de Ecuador: ``'gba1234'`` → ``'GBA-1234'``; ``'GMS429'`` → ``'GMS-0429'``."""
    plate = clean_text(text)
    match = re.fullmatch(r"([A-Z]{3})(\d{3,4})", plate)
    return f"{match.group(1)}-{match.group(2).zfill(4)}" if match else plate


def normalize_plate(raw: str | None,
                    patterns: Sequence[Sequence[int]] = DEFAULT_PATTERNS) -> str | None:
    """Normaliza una lectura al formato ``XXX-0000`` o devuelve ``None`` si no es una placa válida.

    Examples:
        >>> normalize_plate("pba 8901")
        'PBA-8901'
        >>> normalize_plate("ECUADOR GMS-429")
        'GMS-0429'
        >>> normalize_plate("GB01825")
        'GBO-1825'
    """
    plate, is_valid, _ = find_plate(raw, patterns)
    return format_plate(plate) if is_valid else None


def is_valid_plate(plate: str | None) -> bool:
    """``True`` si la placa ya está en el formato canónico ``XXX-0000``."""
    return bool(plate) and bool(_FORMATTED_RE.match(plate))


def plate_distance(a: str | None, b: str | None) -> int:
    """Distancia de Levenshtein entre dos placas, ignorando guiones y mayúsculas.

    Se usa para detectar lecturas que *casi* coinciden con una placa registrada (posible error
    de un carácter del OCR) y para el CER de la evaluación.
    """
    x, y = clean_text(a), clean_text(b)
    try:
        import Levenshtein  # type: ignore

        return int(Levenshtein.distance(x, y))
    except ImportError:  # implementación de respaldo O(n·m)
        previous = list(range(len(y) + 1))
        for i, cx in enumerate(x, start=1):
            current = [i]
            for j, cy in enumerate(y, start=1):
                current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (cx != cy)))
            previous = current
        return previous[-1]


def closest_plate(plate: str, candidates: Iterable[str]) -> tuple[str | None, int]:
    """Devuelve la placa más cercana de ``candidates`` y su distancia (``(None, 99)`` si no hay)."""
    best, best_d = None, 99
    for candidate in candidates:
        d = plate_distance(plate, candidate)
        if d < best_d:
            best, best_d = candidate, d
    return best, best_d


# --------------------------------------------------------------------------------------------
# Imágenes
# --------------------------------------------------------------------------------------------

class ImageValidationError(ValueError):
    """La imagen recibida no se puede procesar (formato, tamaño o contenido)."""


@dataclass(frozen=True)
class ImageLimits:
    """Límites de validación de las imágenes de entrada."""

    max_mb: float = 10.0
    min_side_px: int = 160


def load_image(data: bytes | Image.Image | np.ndarray, limits: ImageLimits = ImageLimits()) -> np.ndarray:
    """Valida una imagen y la devuelve como arreglo RGB ``uint8`` (alto, ancho, 3).

    Acepta bytes (archivo subido o cámara), una imagen de PIL o un arreglo de NumPy.
    Corrige la orientación EXIF de las fotos tomadas con el celular.

    Args:
        data: la imagen en cualquiera de los formatos aceptados.
        limits: tamaño máximo del archivo y lado mínimo en píxeles.

    Returns:
        La imagen RGB como ``np.ndarray``.

    Raises:
        ImageValidationError: si está vacía, es demasiado grande o pequeña, o no es una imagen.
    """
    if data is None:
        raise ImageValidationError("No se recibió ninguna imagen.")
    if isinstance(data, np.ndarray):
        array = data
        if array.ndim == 2:
            array = np.stack([array] * 3, axis=-1)
        if array.ndim != 3 or array.shape[2] not in (3, 4):
            raise ImageValidationError("El arreglo debe tener forma (alto, ancho, 3).")
        array = array[..., :3].astype(np.uint8, copy=False)
    else:
        if isinstance(data, (bytes, bytearray)):
            if len(data) == 0:
                raise ImageValidationError("El archivo está vacío.")
            if len(data) > limits.max_mb * 1024 * 1024:
                raise ImageValidationError(f"La imagen supera {limits.max_mb:g} MB.")
            try:
                image = Image.open(io.BytesIO(data))
                image.load()
            except (UnidentifiedImageError, OSError) as exc:
                raise ImageValidationError("El archivo no es una imagen válida (JPG, PNG o WEBP).") from exc
        elif isinstance(data, Image.Image):
            image = data
        else:
            raise ImageValidationError(f"Tipo de entrada no soportado: {type(data).__name__}")
        image = ImageOps.exif_transpose(image).convert("RGB")
        array = np.asarray(image, dtype=np.uint8)
    height, width = array.shape[:2]
    if min(height, width) < limits.min_side_px:
        raise ImageValidationError(
            f"La imagen es muy pequeña ({width}×{height} px); el lado menor debe tener al menos "
            f"{limits.min_side_px} px.")
    return np.ascontiguousarray(array)


def crop_with_margin(image: np.ndarray, box: Sequence[float], margin: float = 0.06) -> np.ndarray:
    """Recorta ``box`` (x1, y1, x2, y2) agregando un margen relativo y respetando los bordes.

    Args:
        image: imagen RGB.
        box: caja en píxeles.
        margin: fracción del ancho/alto de la caja que se agrega a cada lado.

    Returns:
        El recorte (puede estar vacío si la caja cae fuera de la imagen).
    """
    h, w = image.shape[:2]
    x1, y1, x2, y2 = [float(v) for v in box]
    dx, dy = (x2 - x1) * margin, (y2 - y1) * margin
    x1, y1 = max(0, int(round(x1 - dx))), max(0, int(round(y1 - dy)))
    x2, y2 = min(w, int(round(x2 + dx))), min(h, int(round(y2 + dy)))
    return image[y1:y2, x1:x2].copy()


def letterbox(image: np.ndarray, size: int = 640,
              color: tuple[int, int, int] = (114, 114, 114)) -> tuple[np.ndarray, float, tuple[int, int]]:
    """Redimensiona manteniendo la proporción y rellena hasta ``size``×``size`` (como Ultralytics).

    Returns:
        ``(imagen, escala, (relleno_x, relleno_y))`` para deshacer la transformación de las cajas.
    """
    import cv2

    h, w = image.shape[:2]
    scale = min(size / h, size / w)
    new_w, new_h = int(round(w * scale)), int(round(h * scale))
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    pad_x, pad_y = (size - new_w) // 2, (size - new_h) // 2
    canvas = np.full((size, size, 3), color, dtype=np.uint8)
    canvas[pad_y:pad_y + new_h, pad_x:pad_x + new_w] = resized
    return canvas, scale, (pad_x, pad_y)
