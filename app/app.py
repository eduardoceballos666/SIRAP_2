"""SIRAP – Sistema de Detección y Reconocimiento Automático de Placas (interfaz Streamlit).

Módulos: Dashboard · Reconocimiento y Acceso · Historial · Administración · Acerca del modelo.

Ejecutar desde la raíz del repositorio::

    streamlit run app/app.py

La guía visual es ``docs/img/SIRAP_Dashboard.png``. La lógica (detector, OCR, regla de decisión,
base de datos) vive en ``src/``; este archivo solo arma la interfaz.
"""

from __future__ import annotations

import hashlib
import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from app import ui  # noqa: E402
from src.access_control import AccessDecision, barrier_from_config, decide_access  # noqa: E402
from src.data_processing import ImageLimits, ImageValidationError, load_image, normalize_plate  # noqa: E402
from src.database import Database, DatabaseError  # noqa: E402
from src.model import ALPRPipeline, Recognition  # noqa: E402
from src.utils import get_logger, get_secret, load_config, load_json, now_local  # noqa: E402

st.set_page_config(page_title="SIRAP – Control de acceso", page_icon="🚧", layout="wide",
                   initial_sidebar_state="expanded")

CFG = load_config()
LOG = get_logger("sirap.app")
SAMPLES_DIR = ROOT / "data" / "samples"
THRESHOLD = float(CFG["decision"]["umbral_confianza_ocr"])
DET_THRESHOLD = float((load_json("results/metrics/umbrales.json") or {}).get("YOLO11", {}).get(
    "conf", CFG["detector"].get("conf_decision", 0.30)))
MODULES = ["Dashboard", "Reconocimiento y Acceso", "Historial", "Administración", "Acerca del modelo"]
RESULT_LABELS = {"AUTORIZADO": "Autorizado", "DENEGADO": "Denegado", "NO_REGISTRADO": "No registrado",
                 "VERIFICACION_MANUAL": "Verificación manual"}
RESULT_COLORS = {"Autorizado": "#16a34a", "Denegado": "#dc1f26", "No registrado": "#5b6b85",
                 "Verificación manual": "#d98a00"}
SAMPLES = {
    "Garita 3 · PBA-8901 (lista blanca)": "garita3_PBA-8901.jpg",
    "Garita 2 · GBO-0429 (lista restringida)": "garita2_GBO-0429.jpg",
    "Garita 1 · GSA-1234 (no registrada)": "garita1_GSA-1234.jpg",
    "Garita 3 · imagen desenfocada (verificación)": "garita3_PCD-5678_desenfocada.jpg",
}


# ============================================================================================
# Recursos compartidos
# ============================================================================================
@st.cache_resource(show_spinner="Cargando el detector y el OCR…")
def get_pipeline() -> ALPRPipeline:
    return ALPRPipeline.from_config(CFG)


@st.cache_resource(show_spinner="Conectando con la base de datos…")
def get_db() -> Database:
    return Database.from_environment()


@st.cache_resource
def get_barrier():
    return barrier_from_config(CFG)


def inject_css() -> None:
    css = (ROOT / "app" / "assets" / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def friendly_error(message: str, exc: Exception | None = None) -> None:
    """Muestra un error comprensible y deja el detalle técnico en el log."""
    if exc is not None:
        LOG.exception("%s: %s", message, exc)
    st.error(message, icon="⚠️")


# ============================================================================================
# Barra lateral y encabezado
# ============================================================================================
def sidebar() -> str:
    with st.sidebar:
        st.markdown(
            '<div class="sirap-logo"><div class="frame"><span class="c1"></span><span class="c2"></span>'
            '<span class="word">SIRAP</span></div><div class="sub">Sistema de Detección y Reconocimiento '
            'Automático de Placas</div></div><div class="side-label">MÓDULOS</div>', unsafe_allow_html=True)
        module = st.radio("Módulo", MODULES, index=1, label_visibility="collapsed", key="module")
        try:
            pipeline, db = get_pipeline(), get_db()
            det_dot = "ok" if pipeline.detector.is_model else "warn"
            db_dot = "warn"
            barrier = get_barrier()
            st.markdown(
                f'<div class="side-status"><b>Estado del sistema</b><br>'
                f'<span class="dot {det_dot}"></span>Detector: {pipeline.detector.name}<br>'
                f'<span class="dot ok"></span>OCR: {"afinado (Ecuador)" if "afinado" in pipeline.reader.model_name else "fast-plate-ocr"}<br>'
                f'<span class="dot {db_dot}"></span>Base: "SQLite (demo)"<br>'
                f'<span class="dot {"warn" if getattr(barrier, "simulated", True) else "ok"}"></span>'
                f'Barrera: {"simulada" if getattr(barrier, "simulated", True) else "conectada"}</div>',
                unsafe_allow_html=True)
        except Exception as exc:  # noqa: BLE001
            LOG.exception("Estado del sistema: %s", exc)
    return module


def page_header(title: str) -> None:
    stamp = now_local()
    months = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    hour = stamp.strftime("%I:%M").lstrip("0")
    clock = f"{stamp.day} {months[stamp.month - 1]} {stamp.year}, {hour} {'a. m.' if stamp.hour < 12 else 'p. m.'}"
    st.markdown(f'<div class="page-head"><div><div class="crumb">SIRAP / SISTEMA DE ACCESO</div>'
                f'<div class="page-title">{title}</div></div><div class="page-clock">{clock}</div></div>',
                unsafe_allow_html=True)


# ============================================================================================
# Reconocimiento y Acceso
# ============================================================================================
def _image_input() -> tuple[bytes | None, str]:
    """Selector de fuente: ejemplos precargados, archivo o cámara del navegador."""
    source = st.segmented_control("Fuente de la imagen", ["Ejemplos", "Subir imagen", "Cámara"],
                                  default="Ejemplos", key="source", label_visibility="collapsed")
    if source == "Subir imagen":
        upload = st.file_uploader("Imagen del vehículo (JPG, PNG o WEBP, máx. 10 MB)",
                                  type=CFG["app"]["formatos_imagen"], key="upload")
        return (upload.getvalue() if upload else None), "IMAGEN"
    if source == "Cámara":
        shot = st.camera_input("Capturar vehículo", key="camera")
        return (shot.getvalue() if shot else None), "EN VIVO"
    choice = st.selectbox("Prueba con un ejemplo", list(SAMPLES), key="sample",
                          help="Imágenes de prueba incluidas en data/samples/ (ver data/README.md).")
    return (SAMPLES_DIR / SAMPLES[choice]).read_bytes(), "EJEMPLO"


def _process(data: bytes) -> None:
    """Valida la imagen, corre el pipeline y la regla de decisión; guarda el resultado en sesión."""
    try:
        image = load_image(data, ImageLimits(CFG["app"]["max_tamano_imagen_mb"], CFG["app"]["min_lado_imagen_px"]))
    except ImageValidationError as exc:
        st.session_state.update(rec=None, decision=None, image=None, error=str(exc))
        return
    try:
        with st.spinner("Detectando la placa y leyendo los caracteres…"):
            rec = get_pipeline().recognize(image)
            pipeline = get_pipeline()
            decision = decide_access(rec.plate, rec.ocr_confidence, get_db(), THRESHOLD,
                                     CFG["decision"]["distancia_max_similar"],
                                     det_confidence=rec.det_confidence if pipeline.detector.is_model else None,
                                     det_threshold=DET_THRESHOLD)
    except DatabaseError as exc:
        friendly_error("No se pudo consultar la base de datos. Intente de nuevo o use la apertura manual.", exc)
        return
    except Exception as exc:  # noqa: BLE001
        friendly_error("Ocurrió un problema al procesar la imagen. Pruebe con otra captura.", exc)
        return
    st.session_state.update(rec=rec, decision=decision, image=image, error=None, registered=False,
                            captured_at=now_local(), manual_plate=None)


def _register(accion: str, decision: AccessDecision | None, motivo: str | None = None,
              open_barrier: bool = False) -> None:
    rec: Recognition | None = st.session_state.get("rec")
    garita, operador = st.session_state.get("garita", "Garita 3"), st.session_state.get("operador", "Operador de garita")
    movimiento = st.session_state.get("operacion", "Entrada")
    if not operador.strip():
        st.toast("Escriba el nombre del operador antes de registrar.", icon="⚠️")
        return
    placa_final = st.session_state.get("manual_plate")
    if not placa_final and rec and decision and decision.resultado != "VERIFICACION_MANUAL":
        placa_final = rec.plate  # una lectura dudosa no se guarda como placa confirmada
    try:
        if open_barrier and not get_barrier().open(garita, accion):
            st.error("La barrera no confirmó la apertura. Use la apertura manual de contingencia.")
            return
        get_db().log_operation(
            garita=garita, operador=operador.strip(), tipo_movimiento=movimiento,
            resultado=decision.resultado if decision else "VERIFICACION_MANUAL", accion=accion,
            placa_leida=rec.plate_raw if rec else None, placa_final=placa_final,
            confianza_ocr=rec.ocr_confidence if rec and rec.plate_raw else None,
            lista=decision.lista if decision else None, motivo=motivo,
            origen="MANUAL" if st.session_state.get("manual_plate") or not rec else "DETECCION",
            tiempo_ms=rec.timings_ms.get("total") if rec else None)
    except (DatabaseError, ValueError) as exc:
        friendly_error(f"No se pudo registrar la operación: {exc}", exc)
        return
    st.session_state["registered"] = True
    messages = {"APERTURA_AUTOMATICA": "Operación registrada y barrera abierta.",
                "APERTURA_MANUAL": "Apertura manual registrada en el historial.",
                "RECHAZO": "Rechazo registrado; la barrera permanece cerrada.",
                "SOLO_REGISTRO": "Operación registrada sin abrir la barrera."}
    st.toast(messages.get(accion, "Operación registrada."), icon="✅")


@st.dialog("Apertura manual (Contingencia)")
def manual_dialog() -> None:
    st.markdown("Use esta opción solo si el sistema falla o la situación lo exige. "
                "**La apertura queda registrada con su nombre y el motivo.**")
    motivo = st.text_area("Motivo de la apertura (obligatorio)", max_chars=250,
                          placeholder="Ej.: ambulancia, falla de la cámara, placa ilegible verificada con documentos")
    ok = st.checkbox("Confirmo que verifiqué el vehículo y asumo la apertura manual")
    if st.button("Abrir barrera manualmente", type="primary", disabled=not (ok and len(motivo.strip()) >= 10),
                 width="stretch"):
        _register("APERTURA_MANUAL", st.session_state.get("decision"), motivo.strip(), open_barrier=True)
        st.rerun()
    st.caption("El motivo debe tener al menos 10 caracteres.")


def page_recognition() -> None:
    page_header("Reconocimiento automático y control de acceso")
    pipeline = get_pipeline()
    garita = st.session_state.get("garita", "Garita 3")

    left, right = st.columns([1.72, 1], gap="medium")
    with left, st.container(key="card_camera"):
        head = st.empty()
        data, mode = _image_input()
        if data is not None:
            digest = hashlib.sha1(data).hexdigest()
            if digest != st.session_state.get("digest"):
                st.session_state["digest"] = digest
                _process(data)
        else:
            st.session_state.update(digest=None, rec=None, decision=None, image=None, error=None)
        pill_kind = {"EN VIVO": "live", "EJEMPLO": "img", "IMAGEN": "img"}[mode]
        head.markdown(ui.card_head("camera", f"Cámara en vivo ({garita})", mode, pill_kind), unsafe_allow_html=True)
        if not pipeline.detector.is_model:
            st.markdown('<div class="warn-box">⚠️ <b>Detector de respaldo activo.</b> No se encontraron los pesos de '
                        'YOLO11-s en <code>models/</code>; la placa se localiza con un método clásico de OpenCV, '
                        'menos confiable. Ver <code>models/README.md</code>.</div>', unsafe_allow_html=True)
        if st.session_state.get("error"):
            st.warning(st.session_state["error"], icon="🖼️")
        image = st.session_state.get("image")
        rec: Recognition | None = st.session_state.get("rec")
        decision: AccessDecision | None = st.session_state.get("decision")
        with st.container(key="camera_frame"):
            if image is not None:
                frame = ui.annotate_frame(image, rec.box if rec else None, rec.plate if rec else None,
                                          decision.resultado if decision else None, garita,
                                          st.session_state.get("captured_at", now_local()))
                st.image(frame, width="stretch")
            else:
                st.info("Esperando una imagen: elija un ejemplo, suba una foto o use la cámara.", icon="📷")

    with right:
        with st.container(key="card_result"):
            st.markdown(ui.result_card(decision), unsafe_allow_html=True)
            if decision is not None and decision.motivos:
                st.caption(" · ".join(decision.motivos))
        with st.container(key="card_plate"):
            st.markdown(ui.card_head("car", "Placa identificada"), unsafe_allow_html=True)
            shown = st.session_state.get("manual_plate") or (rec.plate if rec else None)
            conf = 1.0 if st.session_state.get("manual_plate") else (rec.ocr_confidence if rec and rec.plate_raw else None)
            st.markdown(ui.plate_card(shown, conf, THRESHOLD), unsafe_allow_html=True)
            if rec is not None:
                parts = [f"Detector: {rec.detector}"]
                if rec.det_confidence and pipeline.detector.is_model:
                    parts.append(f"conf. detección {rec.det_confidence:.0%}")
                if rec.plate_raw:
                    parts.append(f"lectura OCR «{rec.plate_raw}»")
                parts.append(f"{rec.timings_ms.get('total', 0):.0f} ms")
                st.markdown(f'<div class="meta-line">{" · ".join(parts)}</div>', unsafe_allow_html=True)
                if rec.crop is not None and rec.crop.size:
                    st.image(rec.crop, caption="Recorte enviado al OCR", width=170)
            if decision is not None and decision.resultado != "AUTORIZADO":
                with st.expander("Corregir o escribir la placa manualmente"):
                    typed = st.text_input("Placa (formato ABC-1234)", value=decision.sugerencia or "",
                                          key="typed_plate", max_chars=10)
                    if st.button("Verificar placa", width="stretch"):
                        plate = normalize_plate(typed)
                        if not plate:
                            st.error("Formato inválido: use 3 letras y 3 o 4 dígitos (ej.: PBA-8901).")
                        else:
                            st.session_state["manual_plate"] = plate
                            st.session_state["decision"] = decide_access(plate, 1.0, get_db(), THRESHOLD, 0)
                            st.rerun()

    c1, c2, c3 = st.columns([1, 1.05, 1.1], gap="medium")
    with c1, st.container(key="card_point"):
        st.markdown(ui.card_head("pin", "Datos del punto de control"), unsafe_allow_html=True)
        garitas = get_db().garitas() or CFG["app"]["garitas_por_defecto"]
        st.selectbox("Garita", garitas, index=garitas.index(garita) if garita in garitas else 0, key="garita")
        st.text_input("Operador", value="Operador de garita", key="operador", max_chars=80)
        st.selectbox("Operación", ["Entrada", "Salida"], key="operacion")
    with c2, st.container(key="card_vehicle"):
        st.markdown(ui.card_head("car", "Detalles del vehículo"), unsafe_allow_html=True)
        st.markdown(ui.vehicle_table(decision.vehiculo if decision else None), unsafe_allow_html=True)
    with c3, st.container(key="card_actions"):
        st.markdown(ui.card_head("bolt", "Acciones rápidas"), unsafe_allow_html=True)
        registered = st.session_state.get("registered", False)
        can_open = bool(decision and decision.permite_apertura and not registered)
        with st.container(key="act_open"):
            if st.button("🚧  Registrar y Abrir Barrera", disabled=not can_open, width="stretch",
                         help="Solo se habilita con ACCESO AUTORIZADO; una vez por captura."):
                _register("APERTURA_AUTOMATICA", decision, open_barrier=True)
                st.rerun()
        with st.container(key="act_detect"):
            if st.button("⚙️  Procesar detección automática", width="stretch", disabled=data is None):
                st.session_state["digest"] = None
                st.rerun()
        with st.container(key="act_manual"):
            if st.button("🔒  Apertura manual (Contingencia)", width="stretch"):
                manual_dialog()
        with st.container(key="act_reject"):
            reject_label = "Registrar rechazo" if decision and decision.resultado in ("DENEGADO", "NO_REGISTRADO") \
                else "Registrar sin abrir"
            if st.button(reject_label, width="stretch", disabled=decision is None or registered):
                accion = "RECHAZO" if decision.resultado in ("DENEGADO", "NO_REGISTRADO") else "SOLO_REGISTRO"
                _register(accion, decision)
                st.rerun()
        if registered:
            st.caption("✅ Esta captura ya fue registrada en el historial.")


# ============================================================================================
# Dashboard
# ============================================================================================
def _history(days: int, include_demo: bool) -> pd.DataFrame:
    today = now_local().date()
    df = get_db().operations(desde=today - timedelta(days=days - 1), hasta=today)
    if not include_demo and not df.empty:
        df = df[df["origen"] != "DEMO"]
    if not df.empty:
        df["resultado_txt"] = df["resultado"].map(RESULT_LABELS).fillna(df["resultado"])
    return df


def page_dashboard() -> None:
    page_header("Panel de operaciones")
    f1, f2, _ = st.columns([1.2, 1.4, 2])
    period = f1.selectbox("Periodo", ["Hoy", "Últimos 7 días", "Últimos 30 días"], index=1)
    include_demo = f2.toggle("Incluir operaciones de demostración", value=True,
                             help="Las operaciones DEMO se generan desde Administración para mostrar el panel.")
    days = {"Hoy": 1, "Últimos 7 días": 7, "Últimos 30 días": 30}[period]
    try:
        df = _history(days, include_demo)
    except DatabaseError as exc:
        friendly_error("No se pudo leer el historial.", exc)
        return
    entradas = int((df["tipo_movimiento"] == "ENTRADA").sum()) if not df.empty else 0
    salidas = int((df["tipo_movimiento"] == "SALIDA").sum()) if not df.empty else 0
    identificados = int(df["placa_final"].dropna().nunique()) if not df.empty else 0
    alertas = int(df["resultado"].isin(["DENEGADO", "NO_REGISTRADO"]).sum() + (df["accion"] == "APERTURA_MANUAL").sum()) \
        if not df.empty else 0
    k = st.columns(4)
    k[0].markdown(ui.kpi("Ingresos", entradas, period.lower(), "green"), unsafe_allow_html=True)
    k[1].markdown(ui.kpi("Salidas", salidas, period.lower()), unsafe_allow_html=True)
    k[2].markdown(ui.kpi("Vehículos identificados", identificados, "placas distintas", "yellow"), unsafe_allow_html=True)
    k[3].markdown(ui.kpi("Alertas", alertas, "denegados, no registrados y aperturas manuales", "red"),
                  unsafe_allow_html=True)
    if df.empty:
        st.info("Todavía no hay operaciones en este periodo. Registre accesos en «Reconocimiento y Acceso» "
                "o genere operaciones de demostración en «Administración».", icon="📊")
        return
    st.write("")
    a, b = st.columns([1.6, 1], gap="medium")
    with a, st.container(key="card_chart_hour"):
        st.markdown(ui.card_head("chart", "Operaciones por hora"), unsafe_allow_html=True)
        by_hour = df.assign(hora=df["fecha_hora"].dt.hour).groupby(["hora", "resultado_txt"]).size().reset_index(name="n")
        fig = px.bar(by_hour, x="hora", y="n", color="resultado_txt", color_discrete_map=RESULT_COLORS,
                     labels={"hora": "Hora del día", "n": "Operaciones", "resultado_txt": "Resultado"})
        fig.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10), legend_title_text="",
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", bargap=0.25)
        fig.update_xaxes(dtick=2, range=[-0.5, 23.5])
        st.plotly_chart(fig, width="stretch")
    with b, st.container(key="card_chart_res"):
        st.markdown(ui.card_head("bars", "Resultados de acceso"), unsafe_allow_html=True)
        counts = df["resultado_txt"].value_counts().reset_index()
        counts.columns = ["Resultado", "n"]
        fig = px.pie(counts, names="Resultado", values="n", hole=.55, color="Resultado",
                     color_discrete_map=RESULT_COLORS)
        fig.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)",
                          legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig, width="stretch")
    c, d = st.columns([1, 1.6], gap="medium")
    with c, st.container(key="card_chart_gate"):
        st.markdown(ui.card_head("pin", "Por garita"), unsafe_allow_html=True)
        by_gate = df.groupby(["garita", "tipo_movimiento"]).size().reset_index(name="n")
        fig = px.bar(by_gate, x="n", y="garita", color="tipo_movimiento", orientation="h",
                     color_discrete_map={"ENTRADA": "#2156e8", "SALIDA": "#f7b900"},
                     labels={"n": "Operaciones", "garita": "", "tipo_movimiento": ""})
        fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width="stretch")
    with d, st.container(key="card_alerts"):
        st.markdown(ui.card_head("warn", "Últimas alertas"), unsafe_allow_html=True)
        alerts = df[df["resultado"].isin(["DENEGADO", "NO_REGISTRADO"]) | (df["accion"] == "APERTURA_MANUAL")]
        st.dataframe(alerts[["fecha_hora", "garita", "placa_final", "resultado_txt", "accion", "operador"]].head(12),
                     hide_index=True, width="stretch",
                     column_config={"fecha_hora": st.column_config.DatetimeColumn("Fecha y hora", format="DD/MM HH:mm"),
                                    "placa_final": "Placa", "resultado_txt": "Resultado", "accion": "Acción",
                                    "garita": "Garita", "operador": "Operador"})


# ============================================================================================
# Historial
# ============================================================================================
def page_history() -> None:
    page_header("Historial y auditoría")
    today = now_local().date()
    with st.container(key="card_filters"):
        f = st.columns([1.3, 1, 1, 1.1, 1])
        rango = f[0].date_input("Fechas", (today - timedelta(days=7), today), format="DD/MM/YYYY")
        placa = f[1].text_input("Placa contiene", max_chars=10)
        garitas = ["Todas"] + get_db().garitas()
        garita = f[2].selectbox("Garita", garitas)
        resultado = f[3].selectbox("Resultado", ["Todos"] + list(RESULT_LABELS),
                                   format_func=lambda r: RESULT_LABELS.get(r, r))
        movimiento = f[4].selectbox("Movimiento", ["Todos", "ENTRADA", "SALIDA"])
    desde, hasta = (rango if isinstance(rango, tuple) and len(rango) == 2 else (rango, rango))
    try:
        df = get_db().operations(desde, hasta, placa or None, None if garita == "Todas" else garita,
                                 None if resultado == "Todos" else resultado,
                                 None if movimiento == "Todos" else movimiento)
    except DatabaseError as exc:
        friendly_error("No se pudo consultar el historial.", exc)
        return
    st.caption(f"{len(df)} operaciones encontradas · el historial es de solo inserción (no se edita ni se borra).")
    st.dataframe(df, hide_index=True, width="stretch", height=480,
                 column_config={"fecha_hora": st.column_config.DatetimeColumn("Fecha y hora", format="DD/MM/YYYY HH:mm:ss"),
                                "confianza_ocr": st.column_config.ProgressColumn("Confianza OCR", min_value=0.0,
                                                                                 max_value=1.0, format="percent"),
                                "tiempo_ms": st.column_config.NumberColumn("Tiempo (ms)"), "id": "ID",
                                "garita": "Garita", "operador": "Operador", "tipo_movimiento": "Movimiento",
                                "placa_leida": "Lectura OCR", "placa_final": "Placa", "resultado": "Resultado",
                                "lista": "Lista", "accion": "Acción", "motivo": "Motivo", "origen": "Origen"})
    st.download_button("⬇️  Exportar CSV", df.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"sirap_historial_{today:%Y%m%d}.csv", mime="text/csv", disabled=df.empty)


# ============================================================================================
# Administración
# ============================================================================================
def _admin_unlocked() -> bool:
    pin = get_secret("SIRAP_ADMIN_PIN")
    if not pin:
        st.markdown('<div class="warn-box">Modo demostración: la administración no tiene PIN. En producción defina '
                    '<code>SIRAP_ADMIN_PIN</code> en los secretos.</div>', unsafe_allow_html=True)
        return True
    if st.session_state.get("admin_ok"):
        return True
    typed = st.text_input("PIN de administración", type="password")
    if st.button("Ingresar"):
        st.session_state["admin_ok"] = typed == pin
        if not st.session_state["admin_ok"]:
            st.error("PIN incorrecto.")
        st.rerun()
    return False


def page_admin() -> None:
    page_header("Administración")
    if not _admin_unlocked():
        return
    db = get_db()
    tabs = st.tabs(["Vehículos", "Listas de autorización", "Propietarios", "Garitas", "Usuarios", "Demostración"])
    with tabs[0]:
        st.dataframe(db.table("vehiculos"), hide_index=True, width="stretch")
        with st.form("vehicle_form", clear_on_submit=True):
            st.markdown("**Agregar o actualizar vehículo**")
            c = st.columns(4)
            placa = c[0].text_input("Placa *", max_chars=10)
            marca, modelo, color = c[1].text_input("Marca"), c[2].text_input("Modelo"), c[3].text_input("Color")
            c = st.columns([1, 2, 2])
            tipo = c[0].selectbox("Tipo", ["LIVIANO", "CAMION", "MOTO", "OTRO"])
            propietario, transportista = c[1].text_input("Propietario"), c[2].text_input("Transportista")
            if st.form_submit_button("Guardar vehículo", type="primary"):
                plate = normalize_plate(placa)
                if not plate:
                    st.error("Placa inválida (use 3 letras y 3 o 4 dígitos).")
                else:
                    try:
                        db.upsert_vehicle(plate, marca, modelo, color, tipo, propietario or None, transportista or None)
                        st.success(f"Vehículo {plate} guardado.")
                    except (DatabaseError, ValueError) as exc:
                        friendly_error(f"No se pudo guardar: {exc}", exc)
    with tabs[1]:
        st.dataframe(db.table("autorizaciones"), hide_index=True, width="stretch")
        with st.form("auth_form", clear_on_submit=True):
            st.markdown("**Asignar lista** (reemplaza la autorización vigente de la placa)")
            c = st.columns([1, 1, 2, 1])
            placa = c[0].text_input("Placa *", max_chars=10)
            lista = c[1].selectbox("Lista", ["BLANCA", "RESTRINGIDA"])
            motivo = c[2].text_input("Motivo")
            hasta = c[3].date_input("Vigente hasta", value=None, format="DD/MM/YYYY")
            col_a, col_b = st.columns([1, 1])
            save = col_a.form_submit_button("Guardar autorización", type="primary")
            revoke = col_b.form_submit_button("Quitar de todas las listas")
            plate = normalize_plate(placa)
            if (save or revoke) and not plate:
                st.error("Placa inválida.")
            elif save or revoke:
                try:
                    if save:
                        db.set_authorization(plate, lista, motivo, hasta)
                    else:
                        db.revoke_authorization(plate)
                    st.success("Listas actualizadas.")
                except (DatabaseError, ValueError) as exc:
                    friendly_error(f"No se pudo actualizar: {exc}", exc)
    with tabs[2]:
        st.dataframe(db.table("propietarios"), hide_index=True, width="stretch")
        st.caption("Se guarda el mínimo de datos personales necesario (nombre y un contacto).")
    with tabs[3]:
        st.dataframe(db.table("garitas"), hide_index=True, width="stretch")
        with st.form("gate_form", clear_on_submit=True):
            c = st.columns([1, 2])
            nombre, ubicacion = c[0].text_input("Nombre *"), c[1].text_input("Ubicación")
            if st.form_submit_button("Agregar garita"):
                try:
                    db.add_garita(nombre, ubicacion)
                    st.success("Garita agregada.")
                except (DatabaseError, ValueError) as exc:
                    friendly_error(f"No se pudo agregar: {exc}", exc)
    with tabs[4]:
        st.dataframe(db.table("usuarios"), hide_index=True, width="stretch")
        with st.form("user_form", clear_on_submit=True):
            c = st.columns(3)
            usuario, nombre = c[0].text_input("Usuario *"), c[1].text_input("Nombre *")
            rol = c[2].selectbox("Rol", ["OPERADOR", "SUPERVISOR", "ADMINISTRADOR"])
            if st.form_submit_button("Agregar usuario"):
                try:
                    db.add_user(usuario, nombre, rol)
                    st.success("Usuario agregado.")
                except (DatabaseError, ValueError) as exc:
                    friendly_error(f"No se pudo agregar: {exc}", exc)
    with tabs[5]:
        st.markdown("Genera operaciones **ficticias** marcadas con origen `DEMO` para mostrar el Dashboard. "
                    "No son resultados del modelo ni datos reales; se pueden ocultar en el Dashboard.")
        n = st.slider("Cantidad", 20, 400, 120, step=20)
        if st.button("Generar operaciones de demostración"):
            created = db.load_demo_history(n)
            st.success(f"Se generaron {created} operaciones DEMO en los últimos 7 días.")
        if st.button("Borrar operaciones de demostración"):
            st.success(f"Se borraron {db.clear_demo_history()} operaciones DEMO.")


# ============================================================================================
# Acerca del modelo
# ============================================================================================
def _metric(value, fmt="{:.3f}") -> str:
    return fmt.format(value) if isinstance(value, (int, float)) else "pendiente"


def page_about() -> None:
    page_header("Acerca del modelo")
    pipeline = get_pipeline()
    det = load_json("results/metrics/detector_test.json") or {}
    ocr = load_json("results/metrics/ocr_savh.json") or {}
    e2e = load_json("results/metrics/e2e.json") or {}
    vel = load_json("results/metrics/velocidad.json") or {}
    targets = CFG["metas"]
    a, b = st.columns([1.25, 1], gap="medium")
    with a, st.container(key="card_about"):
        st.markdown(ui.card_head("info", "Cómo funciona"), unsafe_allow_html=True)
        st.markdown(f"""
1. **Detección** – YOLO11-s (Ultralytics, ≈9,4 M parámetros) localiza la placa. Se entrenó con el dataset
   *License Plate Recognition* de Roboflow Universe (v11, 10 125 imágenes, CC BY 4.0), 40 épocas a 640 px
   (0,70 h en una GPU L4).
2. **Lectura (OCR)** – `fast-plate-ocr` con el modelo `{CFG['ocr']['modelo']}` (≈5 MB, CPU) lee los caracteres
   y entrega una probabilidad por carácter; la **confianza OCR** es la menor de ellas (el carácter menos seguro).
3. **Normalización** – la lectura se lleva al formato ecuatoriano `XXX-0000` y se corrigen confusiones
   letra/dígito según la posición (ej. `GB01825 → GBO-1825`).
4. **Decisión** – se consulta la base (SQLite local): lista **restringida** → denegado; lista **blanca**
   vigente → autorizado; detección < {DET_THRESHOLD:.2f}, confianza OCR < {THRESHOLD:.0%} o lectura a un carácter
   de una placa registrada →
   **verificación manual**; en otro caso → no registrado.
5. **Control** – la barrera **nunca** se abre sola: el operador confirma. Todo queda en el historial.

**Detector en uso:** {pipeline.detector.name}
""")
    with b, st.container(key="card_metrics"):
        st.markdown(ui.card_head("bars", "Métricas de rendimiento"), unsafe_allow_html=True)
        rows = [
            ("mAP@0.5 (test)", _metric(det.get("map50")), f"≥ {targets['map50']}"),
            ("mAP@0.5:0.95 (test)", _metric(det.get("map50_95")), "—"),
            ("Precisión / Recall", f"{_metric(det.get('precision'))} / {_metric(det.get('recall'))}", "—"),
            ("F1 detector", _metric(det.get("f1")), "—"),
            ("mAP@0.5:0.95 placas pequeñas", _metric(det.get("map50_95_pequenas")), "—"),
            ("EMR OCR (SAVH Guayaquil, n=399)", _metric(ocr.get("emr"), "{:.1%}"), f"≥ {targets['emr']:.0%}"),
            ("CER OCR (SAVH Guayaquil)", _metric(ocr.get("cer"), "{:.3f}"), "—"),
            ("EMR punta a punta (garita)", _metric(e2e.get("emr"), "{:.1%}"), f"≥ {targets['emr']:.0%}"),
            ("Tiempo por decisión (video garita)", _metric(e2e.get("tiempo_ms_promedio"), "{:.0f} ms"),
             f"≤ {targets['tiempo_e2e_s']:.0f} s"),
            ("Latencia del detector (GPU L4, FP16)", _metric(vel.get("latencia_ms_media"), "{:.1f} ms"), "—"),
        ]
        st.dataframe(pd.DataFrame(rows, columns=["Métrica", "Valor", "Meta"]), hide_index=True, width="stretch")
        st.caption("Valores de results/metrics/*.json, copiados de las salidas del notebook (preset «completo»). "
                   "«pendiente» = medición que todavía no existe (el EMR punta a punta necesita la referencia "
                   "anotada de la garita).")
        hist = ROOT / "results" / "figures" / "resumen_yolo11_completo.png"
        if hist.exists():
            with st.expander("Ver gráficos de evaluación del detector"):
                st.image(str(hist), width="stretch")
    with st.container(key="card_limits"):
        st.markdown(ui.card_head("warn", "Limitaciones y advertencias"), unsafe_allow_html=True)
        st.markdown("""
- El detector se entrenó con placas de varios países; no es específico de Ecuador. El OCR se validó con placas
  reales de **SAVH Guayaquil**, pero su rendimiento baja con placas sucias, dañadas, de noche, muy inclinadas o lejanas.
- Una lectura con confianza baja **no** se decide automáticamente: pasa a verificación manual.
- Las imágenes de ejemplo de esta demo derivan del diseño de la interfaz (ver `data/README.md`); no son capturas reales.
- La barrera de esta versión es **simulada** y la base de demostración contiene datos **ficticios**.
- SIRAP **no** debe usarse para vigilancia masiva, rastreo de personas ni para fines distintos al control de
  acceso de la instalación. Ver `docs/consideraciones_eticas.md`.
""")


# ============================================================================================
# Main
# ============================================================================================
def main() -> None:
    inject_css()
    module = sidebar()
    pages = {"Dashboard": page_dashboard, "Reconocimiento y Acceso": page_recognition, "Historial": page_history,
             "Administración": page_admin, "Acerca del modelo": page_about}
    try:
        pages[module]()
    except Exception as exc:  # noqa: BLE001 — último recurso: nunca mostrar un traceback al operador
        friendly_error("Algo salió mal en este módulo. Recargue la página; si persiste, contacte al administrador.", exc)


if __name__ == "__main__":
    main()
