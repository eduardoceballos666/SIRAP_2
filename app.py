"""
SIRAP – Reconocimiento y Acceso (layout con jerarquía visual)

Nivel 1: video/imagen + placa leída + resultado de autorización
Nivel 2: recorte, confianza, datos del vehículo
Nivel 3: configuración del punto de control (barra lateral)

Reemplaza las funciones `detectar_y_leer` y `consultar_lista` por las del proyecto
(YOLO11 + fast-plate-ocr y la consulta a la lista blanca).
"""

from datetime import datetime

import streamlit as st
from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# Configuración general
# ---------------------------------------------------------------------------
st.set_page_config(page_title="SIRAP – Acceso", layout="wide")

UMBRAL_CONFIANZA = 0.85  # por debajo → REQUIERE VERIFICACIÓN MANUAL

ESTADOS = {
    "AUTORIZADO": {"color": "#1B7F3B", "icono": "✔", "accion": "Abrir barrera"},
    "NO REGISTRADO": {"color": "#C62828", "icono": "✖", "accion": "Registrar rechazo"},
    "REQUIERE VERIFICACIÓN MANUAL": {"color": "#E0A100", "icono": "⚠", "accion": "Verificar manualmente"},
}

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem;}
    .placa {
        font-size: 3.4rem; font-weight: 800; letter-spacing: .12em; text-align: center;
        border: 4px solid #111; border-radius: 10px; padding: .2rem .5rem; background: #fff; color: #111;
    }
    .estado {
        color: #fff; font-size: 1.35rem; font-weight: 800; text-align: center;
        border-radius: 10px; padding: .9rem; margin-top: .6rem;
    }
    .hora {color: #666; font-size: .85rem; text-align: center; margin-top: .3rem;}
    .detalle {font-size: .95rem; margin: .1rem 0;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Funciones del modelo (REEMPLAZAR por las reales)
# ---------------------------------------------------------------------------
def detectar_y_leer(imagen: Image.Image) -> dict | None:
    """Devuelve {'placa', 'confianza', 'bbox': (x1, y1, x2, y2)} o None si no hay placa."""
    w, h = imagen.size
    return {"placa": "PBA-8901", "confianza": 0.98,
            "bbox": (int(w * .42), int(h * .62), int(w * .58), int(h * .72))}


def consultar_lista(placa: str) -> dict | None:
    """Devuelve los datos del vehículo si está en la lista blanca, o None."""
    lista_blanca = {"PBA-8901": {"vehiculo": "Camión Hino 500", "propietario": "Transportes XYZ"}}
    return lista_blanca.get(placa)


def decidir_estado(lectura: dict | None, registro: dict | None) -> str:
    if lectura is None or lectura["confianza"] < UMBRAL_CONFIANZA:
        return "REQUIERE VERIFICACIÓN MANUAL"
    return "AUTORIZADO" if registro else "NO REGISTRADO"


def registrar_evento(**datos):
    """Guardar en el historial (CSV, SQLite, etc.)."""
    st.session_state.setdefault("historial", []).append(datos)


# ---------------------------------------------------------------------------
# Nivel 3: configuración en la barra lateral
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## SIRAP")
    st.caption("Sistema de Detección y Reconocimiento Automático de Placas")
    st.divider()
    garita = st.selectbox("Garita", ["Garita 1", "Garita 2", "Garita 3"], index=2)
    operacion = st.radio("Operación", ["Entrada", "Salida"], horizontal=True)
    operador = st.text_input("Operador", "Operador de garita")
    origen = st.radio("Origen de la captura", ["Subir imagen", "Cámara del navegador"])

st.caption(f"{garita} · {operacion} · {operador}")

# ---------------------------------------------------------------------------
# Captura
# ---------------------------------------------------------------------------
if origen == "Subir imagen":
    archivo = st.sidebar.file_uploader("Imagen", type=["jpg", "jpeg", "png"])
else:
    archivo = st.sidebar.camera_input("Captura")

col_video, col_resultado = st.columns([2, 1], gap="large")

if archivo is None:
    with col_video:
        st.info("Esperando captura de la cámara o una imagen.")
    st.stop()

imagen = Image.open(archivo).convert("RGB")
lectura = detectar_y_leer(imagen)
registro = consultar_lista(lectura["placa"]) if lectura else None
estado = decidir_estado(lectura, registro)
cfg = ESTADOS[estado]
hora = datetime.now().strftime("%H:%M:%S")

# ---------------------------------------------------------------------------
# Nivel 1 (izquierda): video/imagen con la detección
# ---------------------------------------------------------------------------
with col_video:
    vista = imagen.copy()
    if lectura:
        ImageDraw.Draw(vista).rectangle(lectura["bbox"], outline=cfg["color"], width=6)
    st.image(vista, width="stretch")

# ---------------------------------------------------------------------------
# Nivel 1 (derecha): placa + estado  |  Nivel 2: contexto  |  Acciones
# ---------------------------------------------------------------------------
with col_resultado:
    placa_txt = lectura["placa"] if lectura else "— — —"
    st.markdown(f'<div class="placa">{placa_txt}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="estado" style="background:{cfg["color"]}">{cfg["icono"]} {estado}</div>'
        f'<div class="hora">Lectura: {hora}</div>',
        unsafe_allow_html=True,
    )

    st.write("")
    c1, c2 = st.columns([3, 2])
    with c1:
        if lectura:
            st.image(imagen.crop(lectura["bbox"]), caption="Recorte", width="stretch")
    with c2:
        if lectura:
            st.metric("Confianza", f'{lectura["confianza"]:.0%}')

    if registro:
        st.markdown(f'<p class="detalle"><b>Vehículo:</b> {registro["vehiculo"]}</p>'
                    f'<p class="detalle"><b>Propietario:</b> {registro["propietario"]}</p>',
                    unsafe_allow_html=True)
    elif lectura:
        st.markdown('<p class="detalle">Placa sin registro en la lista blanca.</p>',
                    unsafe_allow_html=True)

    st.divider()

    # Acción primaria: una sola, según el estado
    if st.button(cfg["accion"], type="primary", width="stretch"):
        registrar_evento(hora=hora, garita=garita, operacion=operacion, operador=operador,
                         placa=placa_txt, estado=estado, accion=cfg["accion"])
        st.success(f"{cfg['accion']}: registrado.")

    # Acción crítica separada y con confirmación
    with st.expander("Apertura manual (contingencia)"):
        motivo = st.text_input("Motivo", key="motivo")
        confirmar = st.checkbox("Confirmo la apertura manual bajo mi responsabilidad")
        if st.button("Abrir barrera manualmente", disabled=not (confirmar and motivo),
                     width="stretch"):
            registrar_evento(hora=hora, garita=garita, operacion=operacion, operador=operador,
                             placa=placa_txt, estado="CONTINGENCIA", accion=f"Manual: {motivo}")
            st.warning("Apertura manual registrada.")

    # Acción terciaria
    if st.button("Nueva consulta", width="stretch"):
        st.rerun()
