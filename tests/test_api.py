"""Pruebas de la API FastAPI (no afectan a la app de Streamlit)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("jwt")

_TMP = tempfile.mkdtemp(prefix="sirap_api_test_")
os.environ["SIRAP_API_DB"] = str(Path(_TMP) / "api.db")
os.environ["SIRAP_JWT_SECRET"] = "secreto-de-pruebas-0123456789abcdef"
os.environ.pop("", None)

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _token(client, usuario="admin", password="sirap2026"):
    r = client.post("/api/auth/login", json={"usuario": usuario, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_health(client):
    assert client.get("/api/health").json()["estado"] == "ok"


def test_login_rechaza_clave_incorrecta(client):
    r = client.post("/api/auth/login", json={"usuario": "admin", "password": "incorrecta"})
    assert r.status_code == 401


def test_endpoints_protegidos(client):
    assert client.get("/api/system").status_code == 401
    assert client.get("/api/operations", headers={"Authorization": "Bearer xxx"}).status_code == 401


def test_me_y_sistema(client):
    h = _token(client)
    assert client.get("/api/auth/me", headers=h).json()["rol"] == "ADMINISTRADOR"
    s = client.get("/api/system", headers=h).json()
    assert s["barrera"] == "simulada" and s["garitas"]


def test_verificar_placa_manual(client):
    h = _token(client, "operador")
    r = client.post("/api/plates/verify", json={"placa": "pba8901"}, headers=h).json()
    assert r["placa"] == "PBA-8901" and r["decision"]["resultado"] == "AUTORIZADO"
    r = client.post("/api/plates/verify", json={"placa": "GBO-0429"}, headers=h).json()
    assert r["decision"]["resultado"] == "DENEGADO"
    r = client.post("/api/plates/verify", json={"placa": "ZZZ-9999"}, headers=h).json()
    assert r["decision"]["resultado"] == "NO_REGISTRADO"
    assert client.post("/api/plates/verify", json={"placa": "1234"}, headers=h).status_code == 422


def test_reconocer_imagen_de_ejemplo(client):
    h = _token(client, "operador")
    with open(SAMPLES / "garita3_PBA-8901.jpg", "rb") as f:
        r = client.post("/api/recognize", files={"file": ("p.jpg", f, "image/jpeg")}, headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["recognition"]["image_width"] > 0
    assert body["decision"]["resultado"] in ("AUTORIZADO", "DENEGADO", "NO_REGISTRADO", "VERIFICACION_MANUAL")


def test_reconocer_rechaza_archivo_invalido(client):
    h = _token(client, "operador")
    r = client.post("/api/recognize", files={"file": ("x.jpg", b"no es imagen", "image/jpeg")}, headers=h)
    assert r.status_code == 422


def test_operaciones_reglas_del_servidor(client):
    h = _token(client, "operador")
    base = {"garita": "Garita 3", "tipo_movimiento": "ENTRADA", "origen": "MANUAL"}
    # No se puede abrir automáticamente una placa denegada.
    r = client.post("/api/operations", json={**base, "accion": "APERTURA_AUTOMATICA", "placa_final": "GBO-0429"},
                    headers=h)
    assert r.status_code == 409
    # La apertura manual exige motivo.
    r = client.post("/api/operations", json={**base, "accion": "APERTURA_MANUAL", "placa_final": "GBO-0429"},
                    headers=h)
    assert r.status_code == 422
    r = client.post("/api/operations", json={**base, "accion": "APERTURA_AUTOMATICA", "placa_final": "PBA-8901"},
                    headers=h)
    assert r.status_code == 201 and r.json()["barrera_abierta"] is True
    hist = client.get("/api/operations", params={"placa": "PBA-8901"}, headers=h).json()
    assert hist and hist[0]["operador"]


def test_roles(client):
    op = _token(client, "operador")
    assert client.post("/api/admin/garitas", json={"nombre": "Garita X"}, headers=op).status_code == 403
    assert client.get("/api/operations/export.csv", headers=op).status_code == 403
    sup = _token(client, "supervisor")
    r = client.get("/api/operations/export.csv", headers=sup)
    assert r.status_code == 200 and "text/csv" in r.headers["content-type"]


def test_administracion(client):
    h = _token(client)
    r = client.post("/api/admin/vehiculos", json={"placa": "tst-1234", "marca": "Kia", "color": "Rojo"}, headers=h)
    assert r.status_code == 201 and r.json()["placa"] == "TST-1234"
    r = client.post("/api/admin/autorizaciones", json={"placa": "TST-1234", "lista": "BLANCA"}, headers=h)
    assert r.status_code == 201
    v = client.post("/api/plates/verify", json={"placa": "TST-1234"}, headers=h).json()
    assert v["decision"]["resultado"] == "AUTORIZADO"
    assert client.delete("/api/admin/autorizaciones/TST-1234", headers=h).status_code == 200
    assert any(x["placa"] == "TST-1234" for x in client.get("/api/admin/vehiculos", headers=h).json())
    r = client.post("/api/admin/usuarios", json={"usuario": "nuevo", "nombre": "Nuevo", "rol": "OPERADOR",
                                                  "password": "clave-segura"}, headers=h)
    assert r.status_code == 201
    _token(client, "nuevo", "clave-segura")


def test_dashboard_y_modelo(client):
    h = _token(client)
    assert client.post("/api/admin/demo", params={"n": 50}, headers=h).json()["creadas"] > 0
    d = client.get("/api/dashboard", params={"days": 7}, headers=h).json()
    assert set(d["kpis"]) == {"ingresos", "salidas", "identificados", "alertas"}
    assert d["por_resultado"]
    d2 = client.get("/api/dashboard", params={"days": 7, "include_demo": False}, headers=h).json()
    assert d2["kpis"]["ingresos"] <= d["kpis"]["ingresos"]
    assert client.delete("/api/admin/demo", headers=h).json()["borradas"] > 0
    info = client.get("/api/model/info", headers=h).json()
    assert info["metricas"]["detector_test"]


def test_info_del_modelo_incluye_umbrales_y_optimizacion(client):
    info = client.get("/api/model/info", headers=_token(client)).json()
    assert 0 < info["umbral_ocr"] <= 1 and 0 < info["umbral_detector"] < 1
    assert info["metricas"]["optimizacion_resumen"]["mejor_config"]["lr0"] > 0


def test_carga_de_archivo_env(tmp_path, monkeypatch):
    from api.settings import _load_dotenv

    env = tmp_path / ".env"
    env.write_text('# comentario\nSIRAP_PRUEBA_A=uno  # nota\nSIRAP_PRUEBA_B="dos"\nSIRAP_PRUEBA_VACIA=\n', encoding="utf-8")
    monkeypatch.delenv("SIRAP_PRUEBA_A", raising=False)
    monkeypatch.setenv("SIRAP_PRUEBA_B", "ya definida")
    _load_dotenv(env)
    import os

    assert os.environ["SIRAP_PRUEBA_A"] == "uno"
    assert os.environ["SIRAP_PRUEBA_B"] == "ya definida"      # no pisa variables existentes
    assert "SIRAP_PRUEBA_VACIA" not in os.environ
    monkeypatch.delenv("SIRAP_PRUEBA_A")
