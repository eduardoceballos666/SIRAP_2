"""Publica la versión FastAPI + Vue de SIRAP en un Space Docker de Hugging Face.

Lo ejecuta el workflow ``.github/workflows/deploy-hf-space.yml``. Copia solo lo que la imagen necesita (sin notebooks,
documentación ni pesos .pt) y sube la carpeta al Space; Hugging Face construye el ``Dockerfile`` y publica la app.

Variables: ``HF_TOKEN`` (obligatoria, con permiso de escritura), ``HF_SPACE`` (``usuario/nombre``),
``SIRAP_JWT_SECRET`` y ``SIRAP_DEMO_PASSWORD`` (opcionales; se guardan como *secrets* del Space).
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

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
    api = HfApi(token=token)
    api.create_repo(space, repo_type="space", space_sdk="docker", exist_ok=True)
    for name in ("SIRAP_JWT_SECRET", "SIRAP_DEMO_PASSWORD"):
        if os.environ.get(name):
            api.add_space_secret(space, name, os.environ[name])

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        for item in INCLUDE:
            src, dst = ROOT / item, out / item
            if not src.exists():
                print(f"(omitido, no existe) {item}")
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dst, ignore=IGNORE) if src.is_dir() else shutil.copy2(src, dst)
        (out / "data" / "processed").mkdir(parents=True, exist_ok=True)
        (out / "data" / "processed" / ".gitkeep").touch()
        shutil.copy2(Path(__file__).with_name("README.md"), out / "README.md")
        sha = os.environ.get("GITHUB_SHA", "local")[:7]
        api.upload_folder(folder_path=out, repo_id=space, repo_type="space", delete_patterns="*",
                          commit_message=f"Sincronizar desde GitHub ({sha})")
    print(f"Publicado: https://huggingface.co/spaces/{space}")


if __name__ == "__main__":
    main()
