"""Pruebas de normalización de placas y validación de imágenes (src/data_processing.py)."""

import io

import numpy as np
import pytest
from PIL import Image

from src.data_processing import (ImageLimits, ImageValidationError, clean_text, closest_plate, crop_with_margin,
                                 is_valid_plate, letterbox, load_image, normalize_plate, plate_distance)


@pytest.mark.parametrize("raw, expected", [
    ("PBA8901", "PBA-8901"),
    ("pba-8901", "PBA-8901"),
    (" PBA 8901 ", "PBA-8901"),
    ("GMS429", "GMS-0429"),        # placa antigua de 3 dígitos → se completa con 0
    ("GB01825", "GBO-1825"),       # 0 en posición de letra → O
    ("PBA89O1", "PBA-8901"),       # O en posición de dígito → 0
    ("P8A8901", "PBA-8901"),       # 8 en posición de letra → B
])
def test_normalize_plate_valid(raw, expected):
    assert normalize_plate(raw) == expected


@pytest.mark.parametrize("raw", ["", None, "AB123", "PBA89012", "12345678", "ÑÑÑ", "PB-890"])
def test_normalize_plate_invalid(raw):
    assert normalize_plate(raw) is None


def test_is_valid_plate_and_clean_text():
    assert is_valid_plate("PBA-8901")
    assert not is_valid_plate("PBA8901")
    assert clean_text("pba-89_01") == "PBA8901"


def test_plate_distance_and_closest():
    assert plate_distance("PBA-8901", "PBA8901") == 0
    assert plate_distance("PBA-8901", "PBA-8907") == 1
    best, d = closest_plate("PBA-8907", ["GBO-0429", "PBA-8901"])
    assert (best, d) == ("PBA-8901", 1)


def _png_bytes(width=320, height=240):
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (120, 130, 140)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_load_image_ok():
    array = load_image(_png_bytes())
    assert array.shape == (240, 320, 3) and array.dtype == np.uint8


@pytest.mark.parametrize("data, message", [
    (b"", "vacío"),
    (b"esto no es una imagen", "no es una imagen"),
])
def test_load_image_rejects_bad_files(data, message):
    with pytest.raises(ImageValidationError, match=message):
        load_image(data)


def test_load_image_rejects_small_and_large():
    with pytest.raises(ImageValidationError, match="pequeña"):
        load_image(_png_bytes(100, 80))
    with pytest.raises(ImageValidationError, match="supera"):
        load_image(_png_bytes(), ImageLimits(max_mb=0.000001))


def test_crop_with_margin_stays_inside_image():
    image = np.zeros((100, 200, 3), np.uint8)
    crop = crop_with_margin(image, (190, 90, 260, 140), margin=0.2)
    assert crop.shape[0] > 0 and crop.shape[1] > 0
    assert crop.shape[0] <= 100 and crop.shape[1] <= 200


def test_letterbox_shape_and_scale():
    canvas, scale, (pad_x, pad_y) = letterbox(np.zeros((360, 640, 3), np.uint8), 640)
    assert canvas.shape == (640, 640, 3)
    assert scale == pytest.approx(1.0) and pad_x == 0 and pad_y == 140


# Casos de prueba del notebook (sección 2.1): lecturas reales de la cámara de SAVH y textos con la leyenda ECUADOR,
# separadores y símbolos
@pytest.mark.parametrize("raw, expected", [
    ("GS11034", "GSI-1034"), ("6TK6566", "GTK-6566"), ("GTE5D45", "GTE-5045"), ("GP1986", "GPI-0986"),
    ("ECUADOR\nGMS-429", "GMS-0429"), ("EQUIDOR\nGTE-7040", "GTE-7040"), ("ECUNDERG\nGB0-6445", "GBO-6445"),
    ("G5V-3233", "GSV-3233"), ("G50-6164", "GSO-6164"), ("G|G-430", "GIG-0430"), ("GSH+2315", "GSH-2315"),
    ("GTT·4568", "GTT-4568"), ("ECUADOR GMS 429", "GMS-0429"),
])
def test_normalize_plate_notebook_cases(raw, expected):
    assert normalize_plate(raw) == expected


@pytest.mark.parametrize("raw", ["GTT-187G", "GPA-1G88", "OBX=660", "GBΦ6184", "115220", "ECUADOR"])
def test_normalize_plate_rejects_instead_of_inventing(raw):
    """Lecturas que deben ir a verificación manual en vez de convertirse en otra placa válida."""
    assert normalize_plate(raw) is None
