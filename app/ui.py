"""Componentes visuales (HTML/CSS) de la interfaz de SIRAP.

Funciones puras que devuelven HTML o imágenes; no llaman a Streamlit, así se pueden probar.
Todo texto que proviene del usuario o de la base se escapa con ``html.escape``.
"""

from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ICONS = {
    "camera": '<svg viewBox="0 0 24 24"><path d="M17 10.5V7a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-3.5l4 4v-11z"/></svg>',
    "pin": '<svg viewBox="0 0 24 24"><path d="M12 2a7 7 0 0 0-7 7c0 5.2 7 13 7 13s7-7.8 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"/></svg>',
    "car": '<svg viewBox="0 0 24 24"><path d="M18.9 6a1.5 1.5 0 0 0-1.4-1h-11a1.5 1.5 0 0 0-1.4 1L3 12v8a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-1h12v1a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-8l-2.1-6zM6.5 16A1.5 1.5 0 1 1 8 14.5 1.5 1.5 0 0 1 6.5 16zm11 0a1.5 1.5 0 1 1 1.5-1.5 1.5 1.5 0 0 1-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z"/></svg>',
    "bolt": '<svg viewBox="0 0 24 24"><path d="M13 2 4 14h7l-1 8 9-12h-7z"/></svg>',
    "check": '<svg viewBox="0 0 24 24"><path d="M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4z"/></svg>',
    "x": '<svg viewBox="0 0 24 24"><path d="M19 6.4 17.6 5 12 10.6 6.4 5 5 6.4 10.6 12 5 17.6 6.4 19 12 13.4 17.6 19 19 17.6 13.4 12z"/></svg>',
    "question": '<svg viewBox="0 0 24 24"><path d="M11 18h2v-2h-2v2zm1-16a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm0 18a8 8 0 1 1 0-16 8 8 0 0 1 0 16zm0-14a4 4 0 0 0-4 4h2a2 2 0 1 1 4 0c0 2-3 1.75-3 5h2c0-2.25 3-2.5 3-5a4 4 0 0 0-4-4z"/></svg>',
    "warn": '<svg viewBox="0 0 24 24"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>',
    "bars": '<svg viewBox="0 0 24 24"><path d="M4 20h3V12H4v8zm6 0h3V8h-3v12zm6 0h3V4h-3v16z"/></svg>',
    "chart": '<svg viewBox="0 0 24 24"><path d="M3 3h2v16h16v2H3V3zm4 12 4-4 3 3 5-6 1.5 1.3L14 17l-3-3-2.6 2.6L7 15z"/></svg>',
    "list": '<svg viewBox="0 0 24 24"><path d="M4 5h16v2H4zm0 6h16v2H4zm0 6h16v2H4z"/></svg>',
    "info": '<svg viewBox="0 0 24 24"><path d="M11 7h2v2h-2zm0 4h2v6h-2zm1-9a10 10 0 1 0 0 20 10 10 0 0 0 0-20z"/></svg>',
}

#: Estilo por resultado de acceso: (clase CSS, ícono, color RGB para dibujar la caja).
RESULT_STYLE: dict[str, tuple[str, str, tuple[int, int, int]]] = {
    "AUTORIZADO": ("ok", "check", (22, 220, 60)),
    "DENEGADO": ("deny", "x", (230, 30, 40)),
    "NO_REGISTRADO": ("unk", "question", (240, 140, 20)),
    "VERIFICACION_MANUAL": ("manual", "warn", (250, 190, 0)),
}


def card_head(icon: str, title: str, pill: str | None = None, pill_kind: str = "live") -> str:
    """Encabezado de tarjeta: ícono en cuadro oscuro + título + pastilla opcional."""
    pill_html = f'<span class="spacer"></span><span class="pill {pill_kind}">{escape(pill)}</span>' if pill else ""
    return (f'<div class="card-head"><div class="ico">{ICONS[icon]}</div>'
            f'<div class="ttl">{escape(title)}</div>{pill_html}</div>')


def result_card(decision: Any | None) -> str:
    """Tarjeta «Resultado de acceso». ``decision`` es un ``AccessDecision`` o ``None``."""
    if decision is None:
        return (f'<div class="result idle"><div class="badge">{ICONS["camera"]}</div><div>'
                '<div class="lbl">RESULTADO DE ACCESO</div><div class="big" style="color:#8a97ad">EN ESPERA</div>'
                '<div class="sub" style="color:#8a97ad">Seleccione o capture una imagen</div></div></div>')
    css, icon, _ = RESULT_STYLE.get(decision.resultado, ("unk", "question", (0, 0, 0)))
    return (f'<div class="result {css}"><div class="badge">{ICONS[icon]}</div><div>'
            f'<div class="lbl">RESULTADO DE ACCESO</div><div class="big">{escape(decision.titulo)}</div>'
            f'<div class="sub">{escape(decision.detalle)}</div></div></div>')


def plate_card(plate: str | None, confidence: float | None, threshold: float) -> str:
    """Placa grande + barra de confianza OCR (verde ≥ umbral, ámbar ≥ 60 %, rojo < 60 %)."""
    text = escape(plate) if plate else "— — —"
    empty = "" if plate else " empty"
    if confidence is None:
        kind, value = "na", "—"
    else:
        kind = "hi" if confidence >= threshold else ("mid" if confidence >= 0.6 else "lo")
        value = f"{confidence:.0%}"
    return (f'<div class="plate{empty}"><span>{text}</span></div>'
            f'<div class="conf {kind}">{ICONS["bars"]}<span class="t">Confianza OCR:</span>'
            f'<span class="v">{value}</span></div>')


def vehicle_table(vehicle: dict[str, Any] | None) -> str:
    """Tabla clave/valor con marca, modelo, color, propietario (y transportista si existe)."""
    if not vehicle:
        rows = [("Marca", "—"), ("Modelo", "—"), ("Color", "—"), ("Propietario", "No registrado")]
    else:
        rows = [("Marca", vehicle.get("marca")), ("Modelo", vehicle.get("modelo")),
                ("Color", vehicle.get("color")), ("Propietario", vehicle.get("propietario"))]
        if vehicle.get("transportista"):
            rows.append(("Transportista", vehicle.get("transportista")))
    cells = "".join(f"<div>{escape(k)}:</div><div>{escape(str(v or '—'))}</div>" for k, v in rows)
    return f'<div class="kv">{cells}</div>'


def kpi(label: str, value: Any, sub: str = "", color: str = "") -> str:
    """Tarjeta de indicador del Dashboard."""
    return (f'<div class="kpi {color}"><div class="k">{escape(label)}</div><div class="v">{escape(str(value))}</div>'
            f'<div class="s">{escape(sub)}</div></div>')


def _font(size: int) -> ImageFont.ImageFont:
    for name in ("DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "Arial Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow antiguo
        return ImageFont.load_default()


def annotate_frame(image: np.ndarray, box: tuple[float, float, float, float] | None, plate: str | None,
                   resultado: str | None, garita: str, stamp: datetime) -> Image.Image:
    """Dibuja sobre el cuadro la caja de la placa y las etiquetas «Garita» y fecha/hora (como en la guía)."""
    frame = Image.fromarray(image).convert("RGB")
    draw = ImageDraw.Draw(frame, "RGBA")
    w, h = frame.size
    unit = max(12, int(min(w, h) * 0.045))
    if box is not None:
        color = RESULT_STYLE.get(resultado or "", ("", "", (22, 220, 60)))[2]
        thickness = max(3, unit // 5)
        draw.rectangle(box, outline=color + (255,), width=thickness)
        if plate:
            font = _font(int(unit * 0.9))
            tw = draw.textlength(plate, font=font)
            x1, y1 = box[0], max(0, box[1] - unit * 1.4)
            draw.rectangle((x1, y1, x1 + tw + unit * 0.6, y1 + unit * 1.25), fill=color + (235,))
            draw.text((x1 + unit * 0.3, y1 + unit * 0.12), plate, fill=(0, 0, 0), font=font)
    font = _font(int(unit * 0.8))
    pad = unit * 0.45
    for text, anchor_right in ((f"  {garita}", False), (stamp.strftime("%d/%m/%Y   %H:%M:%S"), True)):
        tw = draw.textlength(text, font=font)
        bw, bh = tw + pad * 2, unit * 1.45
        x = w - bw - unit * 0.6 if anchor_right else unit * 0.6
        y = h - bh - unit * 0.6
        draw.rounded_rectangle((x, y, x + bw, y + bh), radius=int(unit * 0.35), fill=(20, 24, 32, 185))
        draw.text((x + pad, y + (bh - unit * 0.95) / 2), text, fill=(255, 255, 255), font=font)
    return frame
