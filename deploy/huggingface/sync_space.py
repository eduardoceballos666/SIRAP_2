"""Publica la versión FastAPI + Vue de SIRAP en un Space Docker de Hugging Face.

Lo ejecuta el workflow ``.github/workflows/deploy-hf-space.yml``. Copia solo lo que la imagen necesita (sin notebooks,
documentación ni pesos .pt) y sube la carpeta al Space; Hugging Face construye el ``Dockerfile`` y publica la app.

Variables: ``HF_TOKEN`` (obligatoria, con permiso de escritura), ``HF_SPACE`` (``usuario/nombre``),
``SIRAP_DATA_GITHUB_TOKEN`` (obligatoria para validar el respaldo privado antes de desplegar),
``SIRAP_JWT_SECRET`` y ``SIRAP_DEMO_PASSWORD`` (opcionales; se guardan como *secrets* del Space).
El flujo valida el token y lo guarda como secreto del Space para que la API acceda al repo privado.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
import json
import urllib.error
import urllib.request

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[2]
INCLUDE = [
    "Dockerfile", ".dockerignore", "requirements.txt", "LICENSE",
    "api", "src", "config", "sql", "frontend", "data/samples", "results/metrics",
    "models/best_model.onnx", "models/README.md",
]
IGNORE = shutil.ignore_patterns("node_modules", "dist", "__pycache__", "*.pyc")


def main() -> None:
    token = os.environ["HF_TOKEN"]
    space = os.environ.get("HF_SPACE") or "eduardoceballos/sirap"
    data_token = os.environ.get("SIRAP_DATA_GITHUB_TOKEN")
    data_repo = os.environ.get("SIRAP_DATA_GITHUB_REPO") or "eduardoceballos666/SIRAP_datos_privados"
    if not data_token:
        raise RuntimeError("Configure el secreto SIRAP_DATA_GITHUB_TOKEN en GitHub Actions antes de desplegar.")
    owner, repo = data_repo.split("/", 1)
    request = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{repo}",
        headers={"Authorization": f"Bearer {data_token}", "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "SIRAP-deploy"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            metadata = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"No se pudo verificar el repositorio privado de datos {data_repo}.") from exc
    if metadata.get("private") is not True:
        raise RuntimeError(f"El repositorio de datos {data_repo} debe ser privado.")
    # El despliegue nunca puede iniciarse con CSV vacíos o antiguos.
    # Verificar los seis archivos existentes ANTES de copiar o reconstruir el Space.
    for file_name in (
        "vehiculos.csv", "autorizaciones.csv", "operaciones.csv",
        "usuarios.csv", "garitas.csv", "credenciales.csv",
    ):
        path = f"/repos/{owner}/{repo}/contents/data/processed/{file_name}"
        file_request = urllib.request.Request(
            "https://api.github.com" + path,
            headers={"Authorization": f"Bearer {data_token}",
                     "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "SIRAP-deploy"},
        )
        try:
            with urllib.request.urlopen(file_request, timeout=20) as response:
                row = json.loads(response.read().decode("utf-8"))
            if row.get("type") != "file" or not row.get("sha"):
                raise ValueError("Archivo remoto inválido.")
        except (urllib.error.URLError, ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"No se desplegará SIRAP: falta o no es legible {file_name} en GitHub privado."
            ) from exc
    api = HfApi(token=token)
    api.create_repo(space, repo_type="space", space_sdk="docker", exist_ok=True)
    for name in ("SIRAP_JWT_SECRET", "SIRAP_DEMO_PASSWORD"):
        if os.environ.get(name):
            api.add_space_secret(space, name, os.environ[name])
    # Autorizado por el propietario: el Space necesita este token para acceder al repo privado.
    api.add_space_secret(space, "SIRAP_DATA_GITHUB_TOKEN", data_token)
    api.add_space_secret(space, "SIRAP_DATA_GITHUB_REPO", data_repo)

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        for item in INCLUDE:
            src, dst = ROOT / item, out / item
            if not src.exists():
                print(f"(omitido, no existe) {item}")
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dst, ignore=IGNORE) if src.is_dir() else shutil.copy2(src, dst)
        processed = out / "data" / "processed"
        processed.mkdir(parents=True, exist_ok=True)
        (processed / ".gitkeep").touch()

        # No incluir CSV operativos ni cuentas predeterminadas en la imagen.
        # El servidor recupera exclusivamente los archivos ya existentes de GitHub privado.
        # El repositorio y su rama de respaldo conservan los registros históricos.
        shutil.copy2(Path(__file__).with_name("README.md"), out / "README.md")
        sha = os.environ.get("GITHUB_SHA", "local")[:7]
        api.upload_folder(folder_path=out, repo_id=space, repo_type="space", delete_patterns="*",
                          commit_message=f"Sincronizar desde GitHub ({sha})")
    print(f"Publicado: https://huggingface.co/spaces/{space}")


if __name__ == "__main__":
    main()
