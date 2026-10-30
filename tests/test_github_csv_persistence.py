"""Validación sin red de GitHub como fuente única de CSV persistentes."""
from __future__ import annotations

import base64
import hashlib
import io

import pandas as pd
import pytest

from src import github_storage
from src.storage import CsvStore, HEADERS, StorageError


@pytest.fixture
def github_remoto(monkeypatch):
    """Simula GitHub Contents API con control de versiones SHA por archivo."""
    monkeypatch.setenv("SIRAP_DATA_GITHUB_TOKEN", "token-solo-pruebas")
    monkeypatch.setenv("SIRAP_GITHUB_REQUIRED", "1")
    monkeypatch.setattr(github_storage, "_verify_private_repository", lambda: None)
    blobs = {}
    for filename, cols in HEADERS.items():
        text = pd.DataFrame(columns=cols).to_csv(index=False)
        blobs[filename + ".csv"] = {"contents": text, "sha": hashlib.sha1(text.encode()).hexdigest()}

    def request(method, path, payload=None):
        name = path.rsplit("/", 1)[-1]
        if name.removesuffix(".csv") not in HEADERS:
            raise AssertionError(f"Ruta no esperada: {path}")
        existing = blobs.get(name)
        if method == "GET":
            if existing is None:
                return None
            return {
                "type": "file", "sha": existing["sha"], "encoding": "base64",
                "content": base64.b64encode(existing["contents"].encode()).decode(),
            }
        if method == "PUT":
            if (payload or {}).get("sha") != (existing or {}).get("sha"):
                raise github_storage.GitHubStorageError("HTTP 409: archivo actualizado por otra sesión")
            text = base64.b64decode(payload["content"]).decode("utf-8")
            sha = hashlib.sha1(text.encode()).hexdigest()
            blobs[name] = {"contents": text, "sha": sha}
            return {"content": {"sha": sha}}
        raise AssertionError(f"Método no esperado: {method}")

    monkeypatch.setattr(github_storage, "_request", request)
    return blobs


def test_restaurar_csv_historico_sin_perder_filas(github_remoto, tmp_path):
    old = pd.DataFrame([{
        "id": "55", "fecha_hora": "2026-10-28 09:10:11", "garita": "Garita 3",
        "operador": "Operador original", "tipo_movimiento": "ENTRADA",
        "placa_final": "PBA-8901", "resultado": "AUTORIZADO",
        "accion": "APERTURA_AUTOMATICA",
    }]).reindex(columns=HEADERS["operaciones"], fill_value="")
    text = old.to_csv(index=False)
    github_remoto["operaciones.csv"] = {
        "contents": text, "sha": hashlib.sha1(text.encode()).hexdigest(),
    }
    store = CsvStore(data_dir=tmp_path)
    assert store.engine == "github-privado"
    assert len(store.operations()) == 1
    assert store.operations().iloc[0]["placa_final"] == "PBA-8901"
    store.log_operation(
        garita="Garita 3", operador="Operador nuevo", tipo_movimiento="SALIDA",
        resultado="AUTORIZADO", accion="SOLO_REGISTRO", placa_final="GSA-1234",
    )
    saved = pd.read_csv(io.StringIO(github_remoto["operaciones.csv"]["contents"]))
    assert len(saved) == 2
    assert saved.iloc[0]["id"] == 55
    assert saved.iloc[0]["placa_final"] == "PBA-8901"
    assert saved.iloc[1]["placa_final"] == "GSA-1234"


def test_sha_desactualizado_no_puede_sobrescribir_cambios(github_remoto, tmp_path):
    first = CsvStore(data_dir=tmp_path / "first")
    second = CsvStore(data_dir=tmp_path / "second")
    a = first._read("vehiculos")
    b = second._read("vehiculos")
    a.loc[len(a), "placa"] = "ABC-1001"
    first._write("vehiculos", a)
    b.loc[len(b), "placa"] = "XYZ-9999"
    with pytest.raises(StorageError, match="Conflicto de versión"):
        second._write("vehiculos", b)
    persisted = pd.read_csv(io.StringIO(github_remoto["vehiculos.csv"]["contents"]), dtype=str)
    assert persisted["placa"].tolist() == ["ABC-1001"]


def test_sin_token_no_arranca_ni_usa_csv_local(github_remoto, monkeypatch, tmp_path):
    monkeypatch.delenv("SIRAP_DATA_GITHUB_TOKEN")
    # Un cache local antiguo NO puede reemplazar datos remotos.
    (tmp_path / "usuarios.csv").write_text("usuario\nusuario-viejo\n")
    with pytest.raises(StorageError, match="GitHub privado"):
        CsvStore(data_dir=tmp_path)


def test_archivo_historico_faltante_no_se_reinicializa(github_remoto, tmp_path):
    del github_remoto["vehiculos.csv"]
    with pytest.raises(StorageError, match="Falta vehiculos.csv"):
        CsvStore(data_dir=tmp_path)
    assert "vehiculos.csv" not in github_remoto


def test_lectura_remota_fallida_no_devuelve_copia_desactualizada(github_remoto, monkeypatch, tmp_path):
    store = CsvStore(data_dir=tmp_path)
    (tmp_path / "operaciones.csv").write_text("id\n1\n")
    old_request = github_storage._request

    def offline(method, path, payload=None):
        if "operaciones.csv" in path:
            raise github_storage.GitHubStorageError("GitHub no disponible")
        return old_request(method, path, payload)

    monkeypatch.setattr(github_storage, "_request", offline)
    with pytest.raises(StorageError, match="GitHub no disponible"):
        store.operations()


def test_csv_de_detecciones_usa_el_mismo_repositorio_privado(github_remoto):
    from src.detection_export import _config
    token, repo, branch, path = _config()
    assert token == "token-solo-pruebas"
    assert repo == "eduardoceballos666/SIRAP_datos_privados"
    assert branch == "main"
    assert path == "data/processed/detecciones.csv"
