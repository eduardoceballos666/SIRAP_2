#!/usr/bin/env python3
"""Reconstruye sin cambios los modelos experimentales SAVH desde .partNNN."""
from pathlib import Path
import hashlib
import shutil

ROOT = Path(__file__).resolve().parent
FILES = {
    "ocr_afinado.onnx": {
        "parts": 3, "size": 4899290,
        "sha256": "40b4aa8bfad222e322d978c2aa0333070fff4c32d9100bef2fc8dd546b3141b2",
    },
    "ocr_afinado.keras": {
        "parts": 9, "size": 16238682,
        "sha256": "362037b3e5cc85fd34a1bfa4b8f05e3e5c551569d0054c66460ae78886b21b0e",
    },
}
for name, expected in FILES.items():
    parts = sorted(ROOT.glob(name + ".part[0-9][0-9][0-9]"))
    if len(parts) != expected["parts"]:
        raise SystemExit(f"{name}: se esperaban {expected['parts']} partes; hay {len(parts)}")
    output = ROOT / name
    temp = ROOT / (name + ".tmp")
    sha = hashlib.sha256()
    with temp.open("wb") as dest:
        for part in parts:
            with part.open("rb") as source:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    dest.write(chunk)
                    sha.update(chunk)
    if temp.stat().st_size != expected["size"] or sha.hexdigest() != expected["sha256"]:
        temp.unlink(missing_ok=True)
        raise SystemExit(f"{name}: falló la comprobación de tamaño o SHA256")
    temp.replace(output)
    print(f"OK: {output.name} ({expected['size']} bytes, SHA256 verificado)")
